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

static RE_DB1E7DE8003A1D790F485A59FF0FD4AC: &[u8] =
    include_bytes!("RE_DB1E7DE8003A1D790F485A59FF0FD4AC.bin");

static RE_44CD3D81020D55D5FF8DD7897F251706: &[u8] =
    include_bytes!("RE_44CD3D81020D55D5FF8DD7897F251706.bin");

#[derive(Debug, PartialEq)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_cond_policy_rule(inp: &Inputs) -> bool {
    (eval_regex(
        &inp.access_subject_subject_id,
        &RE_DB1E7DE8003A1D790F485A59FF0FD4AC,
    )) || (eval_regex(
        &inp.access_subject_subject_id,
        &RE_44CD3D81020D55D5FF8DD7897F251706,
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

    let decision = match evaluate_policy_policy(&inp) {
        Result::Permit => true,
        _ => false,
    };

    env::commit(&decision);
}
