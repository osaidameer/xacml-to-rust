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
    (inp.subject_id == "Julius Hibbert")
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

fn evaluate_cond_rule4(inp: &Inputs) -> bool {
    inp.subject_id == "J. Hibbert"
}

fn evaluate_rule_rule4(inp: &Inputs) -> Result {
    if evaluate_cond_rule4(inp) {
        return Result::Deny;
    } else {
        return Result::NotApplicable;
    }
}

fn evaluate_cond_rule3(inp: &Inputs) -> bool {
    inp.bogus == "Zaphod Beeblebrox"
}

fn evaluate_rule_rule3(inp: &Inputs) -> Result {
    if evaluate_cond_rule3(inp) {
        return Result::Permit;
    } else {
        return Result::NotApplicable;
    }
}

fn evaluate_policy_policy(inp: &Inputs) -> bool {
    let results = vec![
        evaluate_rule_rule1(inp),
        evaluate_rule_rule2(inp),
        evaluate_rule_rule4(inp),
        evaluate_rule_rule3(inp),
    ];

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
