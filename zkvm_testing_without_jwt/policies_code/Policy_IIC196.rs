use chrono::{DateTime, FixedOffset, NaiveDate};
use policy_core::Inputs;
use risc0_zkvm::guest::env;
use std::collections::HashSet;

fn parse_time(raw: &str) -> DateTime<FixedOffset> {
    let input = format!("1970-01-01T{}", raw);
    DateTime::parse_from_rfc3339(&input).unwrap()
}

#[derive(PartialEq)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_cond_policy_rule(inp: &Inputs) -> bool {
    (((vec![parse_time("12:01:02-02:00"), parse_time("08:23:47-05:00")])
        .into_iter()
        .collect::<HashSet<_>>()
        .intersection(
            &inp.access_subject_test_attr
                .iter()
                .map(|x| parse_time(x))
                .collect::<HashSet<_>>(),
        )
        .cloned()
        .collect::<Vec<_>>())
    .len())
        == 2
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
