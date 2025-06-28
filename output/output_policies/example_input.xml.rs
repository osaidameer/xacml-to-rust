use policy_core::Inputs;
use regex::Regex;
use risc0_zkvm::guest::env;

#[derive(Debug)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_target_Allow_Manager_Access(inp: &Inputs) -> bool {
    (("Manager" == inp.role)
        && (Regex::new(r"^192\.168\.1\.[0-9]+$")
            .unwrap()
            .is_match(&inp.ipAddress)))
}

fn evaluate_rule_Allow_Manager_Access(inp: &Inputs) -> Result {
    if !evaluate_target_Allow_Manager_Access(inp) {
        return Result::NotApplicable;
    }

    return Result::Permit;
}

fn evaluate_rule_Deny_All_Others(inp: &Inputs) -> Result {
    return Result::Deny;
}

fn evaluate_target_SamplePolicy(inp: &Inputs) -> bool {
    None
}

fn evaluate_policy_SamplePolicy(inp: &Inputs) -> bool {
    let results = vec![
        evaluate_rule_Allow_Manager_Access(inp),
        evaluate_rule_Deny_All_Others(inp),
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
    let decision = evaluate_policy_SamplePolicy(&inp);
    env::commit(&decision);
}
