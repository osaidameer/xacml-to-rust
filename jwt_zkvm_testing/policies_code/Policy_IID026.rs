use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use base64::Engine;
use policy_core::Inputs;
use risc0_zkvm::guest::env;
use rsa::{
    pkcs1v15::{Signature, VerifyingKey},
    BigUint, RsaPublicKey,
};
use sha2::Sha256;
use signature::Verifier;

use serde::Deserialize;

#[derive(Deserialize)]
struct JwtPayload {
    sub: Option<String>,
    age: Option<String>,
}

fn jwt_field_check(inp: &Inputs, jwt: &JwtPayload) -> bool {
    for field in JWT_FIELD.iter() {
        match *field {
            "sub" => {
                if jwt.sub.as_deref() != Some(inp.access_subject_subject_id.as_str()) {
                    return false;
                }
            }
            "age" => {
                let age_str = inp.access_subject_age.to_string();
                if jwt.age.as_deref() != Some(age_str.as_str()) {
                    return false;
                }
            }
            _ => unreachable!("Unknown field — should be impossible due to codegen"),
        }
    }
    true
}
static MODULUS: &[u8] = include_bytes!("modulus.bin");
static EXPONENT: &[u8] = include_bytes!("exponent.bin");
const JWT_FIELD: &[&str] = &["sub", "age"];

fn extract_jwt(token: &str, inp: &Inputs) -> bool {
    let mut parts = token.split('.');
    let header_b64 = parts.next().expect("jwt header");
    let payload_b64 = parts.next().expect("jwt payload");
    let signature_b64 = parts.next().expect("jwt signature");
    assert!(parts.next().is_none(), "jwt should have exactly 3 parts");

    let engine = URL_SAFE_NO_PAD;
    let _header = engine.decode(header_b64).expect("header base64");
    let payload = engine.decode(payload_b64).expect("payload base64");
    let signature_bytes = engine.decode(signature_b64).expect("signature base64");

    // let n_bytes = engine.decode(MODULUS_B64).expect("modulus base64");
    // let e_bytes = engine.decode(EXPONENT_B64).expect("exponent base64");
    // let n = BigUint::from_bytes_be(&n_bytes);
    // let e = BigUint::from_bytes_be(&e_bytes);

    let n = BigUint::from_bytes_be(MODULUS);
    let e = BigUint::from_bytes_be(EXPONENT);
    let public_key = RsaPublicKey::new(n, e).expect("valid RSA public key");
    let verifying_key = VerifyingKey::<Sha256>::new(public_key);
    let signature = Signature::try_from(signature_bytes.as_slice()).expect("signature format");

    let signed_data = format!("{}.{}", header_b64, payload_b64);
    verifying_key
        .verify(signed_data.as_bytes(), &signature)
        .expect("RSA signature check");

    let payload_str = String::from_utf8(payload).expect("payload utf8");

    // Verify quote positions and extract values

    // this is the case where a policy expects a subject, role, or age field, but the request was missing the required field
    //if positions.is_empty() {
    //    return true;
    //}
    let jwt_struct: JwtPayload = serde_json::from_str(&payload_str).expect("invalid JWT JSON");

    return jwt_field_check(&inp, &jwt_struct);
}

#[derive(PartialEq)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_target_policy1_rule1(inp: &Inputs) -> bool {
    ("J. Hibbert" == inp.access_subject_subject_id)
}

fn evaluate_rule_policy1_rule1(inp: &Inputs) -> Result {
    if !evaluate_target_policy1_rule1(inp) {
        return Result::NotApplicable;
    }

    return Result::Deny;
}

fn evaluate_cond_policy2_rule2(inp: &Inputs) -> bool {
    inp.access_subject_subject_id == "Julius Hibbert"
}

fn evaluate_rule_policy2_rule2(inp: &Inputs) -> Result {
    if evaluate_cond_policy2_rule2(inp) {
        return Result::Deny;
    } else {
        return Result::NotApplicable;
    }
}

fn evaluate_target_policy3_rule3(inp: &Inputs) -> bool {
    ("Zaphod Beeblebrox" == inp.access_subject_bogus)
}

fn evaluate_rule_policy3_rule3(inp: &Inputs) -> Result {
    if !evaluate_target_policy3_rule3(inp) {
        return Result::NotApplicable;
    }

    return Result::Permit;
}

fn evaluate_cond_policy4_rule4(inp: &Inputs) -> bool {
    (inp.access_subject_age - inp.environment_bart_simpson_age) >= 100
}

fn evaluate_rule_policy4_rule4(inp: &Inputs) -> Result {
    if evaluate_cond_policy4_rule4(inp) {
        return Result::Permit;
    } else {
        return Result::NotApplicable;
    }
}

fn evaluate_target_policy1(inp: &Inputs) -> bool {
    ("J. Hibbert" == inp.access_subject_subject_id)
}

fn evaluate_policy_policy1(inp: &Inputs) -> Result {
    if !evaluate_target_policy1(inp) {
        return Result::NotApplicable;
    }

    let results = vec![evaluate_rule_policy1_rule1(inp)];

    //first-applicable
    for res in &results {
        if *res == Result::Permit {
            return Result::Permit;
        } else if *res == Result::Deny {
            return Result::Deny;
        }
    }
    return Result::NotApplicable;
}

fn evaluate_target_policy2(inp: &Inputs) -> bool {
    ("Julius Hibbert" == inp.access_subject_subject_id)
}

fn evaluate_policy_policy2(inp: &Inputs) -> Result {
    if !evaluate_target_policy2(inp) {
        return Result::NotApplicable;
    }

    let results = vec![evaluate_rule_policy2_rule2(inp)];

    //first-applicable
    for res in &results {
        if *res == Result::Permit {
            return Result::Permit;
        } else if *res == Result::Deny {
            return Result::Deny;
        }
    }
    return Result::NotApplicable;
}

fn evaluate_target_policy3(inp: &Inputs) -> bool {
    ("Zaphod Beeblebrox" == inp.access_subject_bogus)
}

fn evaluate_policy_policy3(inp: &Inputs) -> Result {
    if !evaluate_target_policy3(inp) {
        return Result::NotApplicable;
    }

    let results = vec![evaluate_rule_policy3_rule3(inp)];

    //first-applicable
    for res in &results {
        if *res == Result::Permit {
            return Result::Permit;
        } else if *res == Result::Deny {
            return Result::Deny;
        }
    }
    return Result::NotApplicable;
}

fn evaluate_target_policy4(inp: &Inputs) -> bool {
    (100 <= inp.access_subject_age)
}

fn evaluate_policy_policy4(inp: &Inputs) -> Result {
    if !evaluate_target_policy4(inp) {
        return Result::NotApplicable;
    }

    let results = vec![evaluate_rule_policy4_rule4(inp)];

    //first-applicable
    for res in &results {
        if *res == Result::Permit {
            return Result::Permit;
        } else if *res == Result::Deny {
            return Result::Deny;
        }
    }
    return Result::NotApplicable;
}

fn evaluate_policyset_policyset(inp: &Inputs) -> bool {
    //only-one-applicable
    let results = vec![
        evaluate_target_policy1(inp),
        evaluate_target_policy2(inp),
        evaluate_target_policy3(inp),
        evaluate_target_policy4(inp),
    ];
    let mut counter = 0;
    for res in &results {
        if *res == true {
            counter += 1;
            if counter > 1 {
                return false;
            }
        }
        //continues in the case of NotApplicable, condition not needed, adding comment for clarity
    }
    if counter == 1 {
        //return true;
        let results = vec![
            evaluate_policy_policy1(inp),
            evaluate_policy_policy2(inp),
            evaluate_policy_policy3(inp),
            evaluate_policy_policy4(inp),
        ];
        for res in &results {
            if *res == Result::Deny {
                return false;
            }
            if *res == Result::Permit {
                return true;
            }
        }
    }
    return false;
}

fn main() {
    let inp: Inputs = env::read();

    let mut decision = evaluate_policyset_policyset(&inp);

    let jwt: String = env::read();
    if !extract_jwt(&jwt, &inp) {
        decision = false;
    }

    env::commit(&decision);
    env::commit(&inp);
}
