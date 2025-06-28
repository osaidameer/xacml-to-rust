use policy_core::Inputs;
use regex::Regex;
use risc0_zkvm::guest::env;

#[derive(Debug)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_cond_rule(inp: &Inputs) -> bool {
    (Regex::new("J.* Hibbert").unwrap().is_match(&inp.subject_id))
        || (Regex::new("B.* Simpson").unwrap().is_match(&inp.subject_id))
}

fn evaluate_rule_rule(inp: &Inputs) -> Result {
    if evaluate_cond_rule(inp) {
        return Result::Permit;
    } else {
        return Result::NotApplicable;
    }
}

fn evaluate_target_policy(inp: &Inputs) -> bool {
    None
}

fn evaluate_policy_policy(inp: &Inputs) -> bool {
    let results = vec![evaluate_rule_rule(inp)];

    let atleast_one_permit = false;
    for res in &results {
        if *res == Result::Deny {
            return false;
        } else if *res == Result::Permit {
            atleast_one_permit = true;
        }
    }
    return atleast_one_permit;
}

fn main() {
    let inp: Inputs = env::read();
    let decision = evaluate_policy_policy(&inp);
    env::commit(&decision);
}
