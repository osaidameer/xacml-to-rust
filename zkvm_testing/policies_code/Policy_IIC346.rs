use iso8601_duration::Duration as IsoDuration;
use policy_core::Inputs;
use risc0_zkvm::guest::env;
use std::collections::HashSet;

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

#[derive(Debug, PartialEq)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_cond_policy_rule(inp: &Inputs) -> bool {
    (vec![parse_duration("P1Y"), parse_duration("P5Y7M")])
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

    let decision = match evaluate_policy_policy(&inp) {
        Result::Permit => true,
        _ => false,
    };

    env::commit(&decision);
}
