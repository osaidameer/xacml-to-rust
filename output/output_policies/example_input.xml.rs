use policy_core::Inputs;
use regex::Regex;
use risc0_zkvm::guest::env;

#[derive(Debug)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_target_SamplePolicy_Allow_Manager_Access(inp: &Inputs) -> bool {
    (("Manager" == inp.role)
        && (Regex::new(r"^192\.168\.1\.[0-9]+$")
            .unwrap()
            .is_match(&inp.ipAddress)))
}

fn evaluate_rule_SamplePolicy_Allow_Manager_Access(inp: &Inputs) -> Result {
    if !evaluate_target_SamplePolicy_Allow_Manager_Access(inp) {
        return Result::NotApplicable;
    }

    return Result::Permit;
}

fn evaluate_rule_SamplePolicy_Deny_All_Others(inp: &Inputs) -> Result {
    return Result::Deny;
}

fn evaluate_policy_SamplePolicy(inp: &Inputs) -> Result {
    let results = vec![
        evaluate_rule_SamplePolicy_Allow_Manager_Access(inp),
        evaluate_rule_SamplePolicy_Deny_All_Others(inp),
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
