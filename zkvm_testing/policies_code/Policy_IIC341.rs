use chrono::{DateTime, FixedOffset, NaiveDate};
use iso8601_duration::Duration as IsoDuration;
use policy_core::Inputs;
use risc0_zkvm::guest::env;
use std::collections::HashSet;

#[derive(Debug, PartialEq)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}
fn parse_time(raw: &str) -> DateTime<FixedOffset> {
    let input = format!("1970-01-01T{}", raw);
    DateTime::parse_from_rfc3339(&input).unwrap()
}
fn parse_duration(raw: &str) -> String {
    let is_negative = raw.starts_with('-');
    let trimmed = raw.trim_start_matches('-');

    let parsed = IsoDuration::parse(trimmed).unwrap().to_string();

    if is_negative {
        format!("-{}", parsed)
    } else {
        parsed
    }
}

fn evaluate_cond_policy_rule(inp: &Inputs) -> bool {
    (vec![parse_duration("P1DT8H24M"), parse_duration("P5DT2H0M0S")])
        .into_iter()
        .collect::<HashSet<_>>()
        .is_disjoint(
            &inp.access_subject_test_attr
                .iter()
                .map(|x| parse_duration(x))
                .collect::<HashSet<_>>(),
        )
        == false
}

fn evaluate_rule_policy_rule(inp: &Inputs) -> Result {
    if evaluate_cond_policy_rule(inp) {
        return Result::Permit;
    } else {
        return Result::NotApplicable;
    }
}

fn evaluate_policy_policy(inp: &Inputs) -> Result {
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

    let decision = match evaluate_policy_policy(&inp) {
        Result::Permit => true,
        _ => false,
    };

    env::commit(&decision);
}
