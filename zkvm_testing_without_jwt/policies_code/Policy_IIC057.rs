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

static RE_E8667202B740D84E03552D30B7B93A62: &[u8] =
    include_bytes!("RE_E8667202B740D84E03552D30B7B93A62.bin");

static RE_9BAAFAEEB1212012972ABC54D5797FBD: &[u8] =
    include_bytes!("RE_9BAAFAEEB1212012972ABC54D5797FBD.bin");

#[derive(PartialEq)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_cond_policy_rule(inp: &Inputs) -> bool {
    (eval_regex(
        &inp.access_subject_subject_id,
        &RE_E8667202B740D84E03552D30B7B93A62,
    )) || (eval_regex(
        &inp.access_subject_subject_id,
        &RE_9BAAFAEEB1212012972ABC54D5797FBD,
    ))
}

fn evaluate_rule_policy_rule(inp: &Inputs) -> Result {
    if evaluate_cond_policy_rule(inp) {
        return Result::Permit;
    } else {
        return Result::NotApplicable;
    }
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

    let mut decision = match evaluate_policy_policy(&inp) {
        Result::Permit => true,
        _ => false,
    };

    env::commit(&decision);
    env::commit(&inp);
}
