use policy_core::Inputs;
use regex::Regex;
use risc0_zkvm::guest::env;

#[derive(Debug)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_target_rule1(inp: &Inputs) -> bool {
    (inp.subject_id == "J. Hibbert")
}

fn evaluate_rule_rule1(inp: &Inputs) -> Result {
    if !evaluate_target_rule1(inp) {
        return Result::NotApplicable;
    }

    return Result::Deny;
}

fn evaluate_cond_rule2(inp: &Inputs) -> bool {
    (inp.age - inp.bart_simpson_age) >= 5
}

fn evaluate_rule_rule2(inp: &Inputs) -> Result {
    if evaluate_cond_rule2(inp) {
        return Result::Permit;
    } else {
        return Result::NotApplicable;
    }
}

fn main() {
    let inp: Inputs = env::read();
}
