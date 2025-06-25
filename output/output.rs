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

fn main() {
    let inp: Inputs = env::read();
}
