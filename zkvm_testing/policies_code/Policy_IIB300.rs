use policy_core::Inputs;
use risc0_zkvm::guest::env;

#[derive(Debug, PartialEq)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_rule_policy_rule(inp: &Inputs) -> Result {
    return Result::Permit;
}

fn evaluate_target_policy(inp: &Inputs) -> bool {
    ((("read" == inp.action_action_id) || ("write" == inp.action_action_id))
        && ("doctor" == inp.access_subject_role && "medical record" == inp.resource_resource_type))
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

fn evaluate_policyset_policyset(inp: &Inputs) -> bool {
    let results = vec![evaluate_policy_policy(inp)];

    //deny-overrides
    let mut atleast_one_permit = false;
    for res in &results {
        if *res == Result::Deny {
            return false;
        } else if *res == Result::Permit {
            atleast_one_permit = true;
        }
    }
    return atleast_one_permit;
}

fn main() {
    let inp: Inputs = env::read();

    let decision = evaluate_policyset_policyset(&inp);

    env::commit(&decision);
}
