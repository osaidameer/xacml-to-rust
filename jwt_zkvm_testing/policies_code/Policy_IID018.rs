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

static MODULUS: &[u8] = include_bytes!("modulus.bin");
static EXPONENT: &[u8] = include_bytes!("exponent.bin");

fn verify_jwt(token: &str) {
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
}

#[derive(Debug, PartialEq)]
enum Result {
    Permit,
    Deny,
    NotApplicable,
}

fn evaluate_target_policy_rule1(inp: &Inputs) -> bool {
    ("J. Hibbert" == inp.access_subject_subject_id)
}

fn evaluate_rule_policy_rule1(inp: &Inputs) -> Result {
    if !evaluate_target_policy_rule1(inp) {
        return Result::NotApplicable;
    }

    return Result::Deny;
}

fn evaluate_cond_policy_rule2(inp: &Inputs) -> bool {
    inp.access_subject_subject_id == "Julius Hibbert"
}

fn evaluate_rule_policy_rule2(inp: &Inputs) -> Result {
    if evaluate_cond_policy_rule2(inp) {
        return Result::Deny;
    } else {
        return Result::NotApplicable;
    }
}

fn evaluate_target_policy_rule3(inp: &Inputs) -> bool {
    ("Zaphod Beeblebrox" == inp.access_subject_bogus)
}

fn evaluate_rule_policy_rule3(inp: &Inputs) -> Result {
    if !evaluate_target_policy_rule3(inp) {
        return Result::NotApplicable;
    }

    return Result::Permit;
}

fn evaluate_cond_policy_rule4(inp: &Inputs) -> bool {
    (inp.access_subject_age - inp.environment_bart_simpson_age) >= 5
}

fn evaluate_rule_policy_rule4(inp: &Inputs) -> Result {
    if evaluate_cond_policy_rule4(inp) {
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

    let results = vec![
        evaluate_rule_policy_rule1(inp),
        evaluate_rule_policy_rule2(inp),
        evaluate_rule_policy_rule3(inp),
        evaluate_rule_policy_rule4(inp),
    ];

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

fn main() {
    let inp: Inputs = env::read();
    let jwt: String = env::read();
    verify_jwt(&jwt);

    let decision = match evaluate_policy_policy(&inp) {
        Result::Permit => true,
        _ => false,
    };

    env::commit(&decision);
}
