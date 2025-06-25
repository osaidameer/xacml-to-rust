use policy_core::Inputs;
use regex::Regex;
use risc0_zkvm::guest::env;

#[derive(Debug)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_target_rule(inp: &Inputs) -> bool {
    ((inp.subject_id == "Julius Hibbert")
        && (inp.resource_id == "http://medico.com/record/patient/BartSimpson")
        && ((inp.action_id == "read") || (inp.action_id == "write")))
}

fn evaluate_rule_rule(inp: &Inputs) -> Result {
    if !evaluate_target_rule(inp) {
        return Result::NotApplicable;
    }

    return Result::Permit;
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
