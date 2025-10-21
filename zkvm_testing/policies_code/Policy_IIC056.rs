use policy_core::Inputs;
use regex_automata::dfa::{dense::DFA, Automaton};
use regex_automata::Input;
use risc0_zkvm::guest::env;

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

static RE_ED4C7C001BB380B1CA8A333D4E2D69A9: &[u8] =
    include_bytes!("RE_ED4C7C001BB380B1CA8A333D4E2D69A9.bin");

static RE_3FC2A4F9B76EEC7F4B2CF2413AF34EFA: &[u8] =
    include_bytes!("RE_3FC2A4F9B76EEC7F4B2CF2413AF34EFA.bin");

#[derive(Debug, PartialEq)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_cond_policy_rule(inp: &Inputs) -> bool {
    (eval_regex(
        &inp.access_subject_subject_id,
        &RE_ED4C7C001BB380B1CA8A333D4E2D69A9,
    )) || (eval_regex(
        &inp.access_subject_subject_id,
        &RE_3FC2A4F9B76EEC7F4B2CF2413AF34EFA,
    ))
}

fn evaluate_rule_policy_rule(inp: &Inputs) -> Result {
    if evaluate_cond_policy_rule(inp) {
        return Result::Permit;
    } else {
        return Result::NotApplicable;
    }
}

fn evaluate_policy_policy(inp: &Inputs) -> Result {
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
