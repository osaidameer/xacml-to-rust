use policy_core::Inputs;
use risc0_zkvm::guest::env;

fn jwt_field_check(inp: &Inputs, extracted_values: &[String]) -> bool {
    for (i, field) in JWT_FIELD.iter().enumerate() {
        match *field {
            "age" => {
                if extracted_values[i].parse() != Ok(inp.access_subject_age) {
                    return false;
                }
            }
            _ => unreachable!("Unknown field — should be impossible due to codegen"),
        }
    }
    true
}

#[derive(Debug, PartialEq)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_cond_policy_rule(inp: &Inputs) -> bool {
    inp.access_subject_age == 45
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

    let mut decision = match evaluate_policy_policy(&inp) {
        Result::Permit => true,
        _ => false,
    };

    env::commit(&decision);
    env::commit(&inp);
}
