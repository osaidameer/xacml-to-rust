use policy_core::Inputs;
use risc0_zkvm::guest::env;

use regex_automata::dfa::{dense::DFA, Automaton};
use regex_automata::Input;

fn eval_regex(regex_input: &str, regex_exp: &[u8]) -> bool {
    match DFA::from_bytes(regex_exp) {
        Ok((dfa, _)) => {
            let input = Input::new(regex_input);
            match dfa.try_search_fwd(&input) {
                Ok(result) => result.is_some(),
                Err(_) => false,
            }
        }
        Err(_) => false,
    }
}

static RE_0D7FE33937DB69EB4A2BFA203B7B3734: &[u8] =
    include_bytes!("RE_0D7FE33937DB69EB4A2BFA203B7B3734.bin");

#[derive(Debug, PartialEq)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_target_policy_rule(inp: &Inputs) -> bool {
    (("Julius Hibbert" == inp.access_subject_subject_id)
        && ("http://medico.com/record/patient/BartSimpson" == inp.resource_resource_id)
        && (eval_regex(&inp.action_action_id, &RE_0D7FE33937DB69EB4A2BFA203B7B3734)))
}

fn evaluate_rule_policy_rule(inp: &Inputs) -> Result {
    if !evaluate_target_policy_rule(inp) {
        return Result::NotApplicable;
    }

    return Result::Permit;
}

fn evaluate_target_policy(inp: &Inputs) -> bool {
    true
}

fn evaluate_policy_policy(inp: &Inputs) -> Result {
    if !evaluate_target_policy(inp) {
        return Result::NotApplicable;
    }

    let results = vec![evaluate_rule_policy_rule(inp)];

    //deny-overrides
    let mut atleast_one_permit = false;
    for res in &results {
        if *res == Result::Deny {
            return Result::Deny;
        } else if *res == Result::Permit {
            atleast_one_permit = true;
        }
    }
    if atleast_one_permit {
        return Result::Permit;
    }
    return Result::NotApplicable;
}

fn main() {
    let inp: Inputs = env::read();

    let decision = match evaluate_policy_policy(&inp) {
        Result::Permit => true,
        _ => false,
    };

    env::commit(&decision);
}
