package agentos.pii

# Redact email addresses
redact_field[field] {
    input.field == field
    regex.match("^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$", input.value)
}

# Redact SSN
redact_field[field] {
    input.field == field
    regex.match("^\\d{3}-\\d{2}-\\d{4}$", input.value)
}
