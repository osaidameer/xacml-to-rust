# XACML to Rust

A code generator which parses an XACML Policy into an intermediate representation, primarily based on a logical expression tree. This IR is then converted into rust programs designed to run inside a zkvm.

## Modules

### Intermediate Representation

This module parses XACML policies and transforms them into a structured intermediate representation (IR). The IR models the policy as a logical expression tree, capturing policy sets, policies, conditions, rules, and targets in a format tailored towards code generation.

### Code Generator

This module takes the intermediate representation (IR) as input and generates Rust code that implements the policy logic. Supports most comparison operators, regex, and binary operations, and utilizes Jinja templates for structured, readable code generation. 

## Tech Stack

- Python: Used for parsing XACML policies, generating the intermediate representation (IR), and generating output
- Jinja: Template engine used to aid code generation
- Rust: Output language for generated code

## Installation


1. **Clone the repository:**

   ```bash
   git clone https://github.com/osaidameer/xacml-to-rust.git
   cd your-repo-name
    ```

2. **Setup Python environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate # On Windows use: venv\Scripts\activate
   ```
3. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
    ```

4. **Install rust (if not installed already)**
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```
5. **Install Rustfmt (Used for formatting rust output file)**
   ```bash
   rustup component add rustfmt
    ```
6. **Run tool**
    ```bash
   python3 main.py path/to/policy.xml
   ```
   
## Usage Example
   ```bash
   python3 main.py policies/Policy_A01.xml
   ```

## Limitations
- Currently missing date duration, bag, set, string manipulation, and type conversion functions
- Missing rfc800Name, x500path as data types
- Does not currently support nested PolicySets
- Limited support for custom XACML functions

## TODO
- Design testing pipeline to run all test cases from collected dataset
  - Define input format from request.xml in dataset
- Handle case where attribute is not present in request, based on decided input format
- Add string manipulation functionality. Clean up rust_expr function and merge after completion

