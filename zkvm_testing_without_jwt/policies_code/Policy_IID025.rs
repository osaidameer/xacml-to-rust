use policy_core::Inputs;
use risc0_zkvm::guest::env;

#[derive(PartialEq)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_rule_policy1_rule1(inp: &Inputs) -> Result {
    return Result::Deny;
}

fn evaluate_cond_policy2_rule2(inp: &Inputs) -> bool {
    (inp.access_subject_age - inp.environment_bart_simpson_age) >= 5
}

fn evaluate_rule_policy2_rule2(inp: &Inputs) -> Result {
    if evaluate_cond_policy2_rule2(inp) {
        return Result::Permit;
    } else {
        return Result::NotApplicable;
    }
}

fn evaluate_target_policy1(inp: &Inputs) -> bool {
    ("J. Hibbert" == inp.access_subject_subject_id)
}

fn evaluate_policy_policy1(inp: &Inputs) -> Result {
    if !evaluate_target_policy1(inp) {
        return Result::NotApplicable;
    }

    let results = vec![evaluate_rule_policy1_rule1(inp)];

    //first-applicable
    for res in &results {
        if *res == Result::Permit {
            return Result::Permit;
        } else if *res == Result::Deny {
            return Result::Deny;
        }
    }
    return Result::NotApplicable;
}

fn evaluate_target_policy2(inp: &Inputs) -> bool {
    true
}

fn evaluate_policy_policy2(inp: &Inputs) -> Result {
    if !evaluate_target_policy2(inp) {
        return Result::NotApplicable;
    }

    let results = vec![evaluate_rule_policy2_rule2(inp)];

    //first-applicable
    for res in &results {
        if *res == Result::Permit {
            return Result::Permit;
        } else if *res == Result::Deny {
            return Result::Deny;
        }
    }
    return Result::NotApplicable;
}

fn evaluate_policyset_policyset(inp: &Inputs) -> bool {
    //only-one-applicable
    let results = vec![evaluate_target_policy1(inp), evaluate_target_policy2(inp)];
    let mut counter = 0;
    for res in &results {
        if *res == true {
            counter += 1;
            if counter > 1 {
                return false;
            }
        }
        //continues in the case of NotApplicable, condition not needed, adding comment for clarity
    }
    if counter == 1 {
        //return true;
        let results = vec![evaluate_policy_policy1(inp), evaluate_policy_policy2(inp)];
        for res in &results {
            if *res == Result::Deny {
                return false;
            }
            if *res == Result::Permit {
                return true;
            }
        }
    }
    return false;
}

fn main() {
    let inp: Inputs = env::read();

    let mut decision = evaluate_policyset_policyset(&inp);

    env::commit(&decision);
    env::commit(&inp);
}
