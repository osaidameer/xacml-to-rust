use policy_core::Inputs;
use risc0_zkvm::guest::env;

#[derive(PartialEq)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_target_policy_rule(inp: &Inputs) -> bool {
    (("Julius Hibbert" == inp.access_subject_subject_id
        && "riddle me this" == inp.access_subject_some_attribute)
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
