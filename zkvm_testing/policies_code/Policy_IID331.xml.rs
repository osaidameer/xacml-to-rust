use policy_core::Inputs;
use risc0_zkvm::guest::env;

#[derive(Debug, PartialEq)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_target_policy1_rule1(inp: &Inputs) -> bool {
    ("J. Hibbert" == inp.access_subject_subject_id)
}

fn evaluate_rule_policy1_rule1(inp: &Inputs) -> Result {
    if !evaluate_target_policy1_rule1(inp) {
        return Result::NotApplicable;
    }

    return Result::Deny;
}

fn evaluate_cond_policy2_rule2(inp: &Inputs) -> bool {
    (inp.access_subject_age - inp.environment_bart_simpson_age) >= 55
}

fn evaluate_rule_policy2_rule2(inp: &Inputs) -> Result {
    if evaluate_cond_policy2_rule2(inp) {
        return Result::Permit;
    } else {
        return Result::NotApplicable;
    }
}

fn evaluate_cond_policy3_rule3(inp: &Inputs) -> bool {
    inp.access_subject_test == "Zaphod Beedlebrox"
}

fn evaluate_rule_policy3_rule3(inp: &Inputs) -> Result {
    if evaluate_cond_policy3_rule3(inp) {
        return Result::Permit;
    } else {
        return Result::NotApplicable;
    }
}

fn evaluate_cond_policy4_rule4(inp: &Inputs) -> bool {
    inp.access_subject_subject_id == "Julius Hibbert"
}

fn evaluate_rule_policy4_rule4(inp: &Inputs) -> Result {
    if evaluate_cond_policy4_rule4(inp) {
        return Result::Deny;
    } else {
        return Result::NotApplicable;
    }
}

fn evaluate_cond_policy5_rule2(inp: &Inputs) -> bool {
    (inp.access_subject_age - inp.environment_bart_simpson_age) >= 5
}

fn evaluate_rule_policy5_rule2(inp: &Inputs) -> Result {
    if evaluate_cond_policy5_rule2(inp) {
        return Result::Permit;
    } else {
        return Result::NotApplicable;
    }
}

fn evaluate_policy_policy1(inp: &Inputs) -> Result {
    let results = vec![evaluate_rule_policy1_rule1(inp)];

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

fn evaluate_policy_policy2(inp: &Inputs) -> Result {
    let results = vec![evaluate_rule_policy2_rule2(inp)];

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

fn evaluate_policy_policy3(inp: &Inputs) -> Result {
    let results = vec![evaluate_rule_policy3_rule3(inp)];

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

fn evaluate_policy_policy4(inp: &Inputs) -> Result {
    let results = vec![evaluate_rule_policy4_rule4(inp)];

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

fn evaluate_policy_policy5(inp: &Inputs) -> Result {
    let results = vec![evaluate_rule_policy5_rule2(inp)];

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

fn evaluate_policyset_policyset(inp: &Inputs) -> bool {
    let results = vec![
        evaluate_policy_policy1(inp),
        evaluate_policy_policy2(inp),
        evaluate_policy_policy3(inp),
        evaluate_policy_policy4(inp),
        evaluate_policy_policy5(inp),
    ];

    //permit-overrides || deny-unless-permit
    for res in &results {
        if *res == Result::Permit {
            return true;
        }
    }
    return false;
}

fn main() {
    let inp: Inputs = env::read();

    let decision = evaluate_policyset_policyset(&inp);

    env::commit(&decision);
}
