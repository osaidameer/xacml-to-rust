use policy_core::Inputs;
use regex::Regex;
use risc0_zkvm::guest::env;

#[derive(Debug)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_target_policy_rule1(inp: &Inputs) -> bool {
    ("Julius Hibbert" == inp.subject_id)
}

fn evaluate_rule_policy_rule1(inp: &Inputs) -> Result {
    if !evaluate_target_policy_rule1(inp) {
        return Result::NotApplicable;
    }

    return Result::Deny;
}

fn evaluate_cond_policy_rule2(inp: &Inputs) -> bool {
    (inp.age - inp.bart_simpson_age) >= 5
}

fn evaluate_rule_policy_rule2(inp: &Inputs) -> Result {
    if evaluate_cond_policy_rule2(inp) {
        return Result::Permit;
    } else {
        return Result::NotApplicable;
    }
}

fn evaluate_cond_policy_rule4(inp: &Inputs) -> bool {
    inp.subject_id == "J. Hibbert"
}

fn evaluate_rule_policy_rule4(inp: &Inputs) -> Result {
    if evaluate_cond_policy_rule4(inp) {
        return Result::Deny;
    } else {
        return Result::NotApplicable;
    }
}

fn evaluate_cond_policy_rule3(inp: &Inputs) -> bool {
    inp.bogus == "Zaphod Beeblebrox"
}

fn evaluate_rule_policy_rule3(inp: &Inputs) -> Result {
    if evaluate_cond_policy_rule3(inp) {
        return Result::Permit;
    } else {
        return Result::NotApplicable;
    }
}

fn evaluate_policy_policy(inp: &Inputs) -> Result {
    let results = vec![
        evaluate_rule_rule1(inp),
        evaluate_rule_rule2(inp),
        evaluate_rule_rule4(inp),
        evaluate_rule_rule3(inp),
    ];

    //deny-overrides
    let atleast_one_permit = false;
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

    let decision = false;
    let intermediate = evaluate_policy_policy(&inp);
    if *intermediate == Result::Permit {
        decision = true;
    } else {
        decision = false;
    }

    env::commit(&decision);
}
