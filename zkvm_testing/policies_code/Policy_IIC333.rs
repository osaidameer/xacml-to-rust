use policy_core::Inputs;
use risc0_zkvm::guest::env;

#[derive(Debug, PartialEq)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn substring_helper(input: &str, start: i32, end: i32) -> Option<&str> {
    if start < 0 || end < -1 {
        return None;
    }
    let start_size = start as usize;
    let end_size = if end == -1 { input.len() } else { end as usize };
    if start_size > end_size || end_size > input.len() {
        return None;
    }
    Some(&input[start_size..end_size])
}

fn evaluate_cond_policy_rule(inp: &Inputs) -> bool {
    (substring_helper("http://this/is/the/initial/uri", 14, 24).unwrap_or("")) == "/the/initi"
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
