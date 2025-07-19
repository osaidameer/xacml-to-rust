use policy_core::Inputs;
use risc0_zkvm::guest::env;

#[derive(Debug, PartialEq)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_target_policy_rule1(inp: &Inputs) -> bool {
    ("J. Hibbert" == inp.access_subject_subject_id)
}

fn evaluate_rule_policy_rule1(inp: &Inputs) -> Result {
    if !evaluate_target_policy_rule1(inp) {
        return Result::NotApplicable;
    }

    return Result::Deny;
}

fn evaluate_cond_policy_rule2(inp: &Inputs) -> bool {
    (inp.access_subject_age - inp.environment_bart_simpson_age) >= 55
}

fn evaluate_rule_policy_rule2(inp: &Inputs) -> Result {
    if evaluate_cond_policy_rule2(inp) {
        return Result::Permit;
    } else {
        return Result::NotApplicable;
    }
}

fn evaluate_cond_policy_rule3(inp: &Inputs) -> bool {
    inp.access_subject_test == "Zaphod Beedlebrox"
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
        evaluate_rule_policy_rule1(inp),
        evaluate_rule_policy_rule2(inp),
        evaluate_rule_policy_rule3(inp),
    ];

    //permit-overrides || deny-unless-permit
    let mut atleast_one_deny = false;
    for res in &results {
        if *res == Result::Permit {
            return Result::Permit;
        } else if *res == Result::Deny {
            atleast_one_deny = true;
        }
    }
    if atleast_one_deny {
        return Result::Deny;
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
