use chrono::{DateTime, FixedOffset, NaiveDate};
use policy_core::Inputs;
use risc0_zkvm::guest::env;

fn jwt_field_check(inp: &Inputs, extracted_values: &[String]) -> bool {
    for (i, field) in JWT_FIELD.iter().enumerate() {
        match *field {
            "sub" => {
                if extracted_values[i] != inp.access_subject_subject_id {
                    return false;
                }
            }
            _ => unreachable!("Unknown field — should be impossible due to codegen"),
        }
    }
    true
}
fn parse_time(raw: &str) -> DateTime<FixedOffset> {
    let input = format!("1970-01-01T{}", raw);
    DateTime::parse_from_rfc3339(&input).unwrap()
}

#[derive(Debug, PartialEq)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_target_policy_rule(inp: &Inputs) -> bool {
    (("Julius Hibbert" == inp.access_subject_subject_id
        && "2002-02-08T08:23:47-05:00"
            .parse::<DateTime<FixedOffset>>()
            .unwrap()
            == inp.access_subject_request_time)
        && ("http://medico.com/record/patient/BartSimpson" == inp.resource_resource_id)
        && (("read" == inp.action_action_id) || ("write" == inp.action_action_id)))
}

fn evaluate_rule_policy_rule(inp: &Inputs) -> Result {
    if !evaluate_target_policy_rule(inp) {
        return Result::NotApplicable;
    }

    return Result::Permit;
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
