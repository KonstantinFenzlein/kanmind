let signUpValues = {
    "fullname": "",
    "email": "",
    "password": "",
    "repeated_password": ""
}

async function signUpSubmit(event) {
    event.preventDefault();
    let isFormValid = validateSignUp();
    if (isFormValid) {
        registration(signUpValues)
    }
}

async function registration(data) {
    let response = await postData(REGISTER_URL, data);
    if (!response.ok) {
        let errorArr = extractErrorMessages(response.data)
        showToastMessage(true, errorArr)
    } else {
        setAuthCredentials(response.data.token, response.data.user_id, response.data.email, response.data.fullname)
        window.location.href = "../dashboard/index.html"
    }
}

async function logInSubmit(event) {
    event.preventDefault();
    setError(false, "error_login")
    const data = getFormData(event.target);
    await logIn(data)
}

async function logIn(data) {
    let response = await postData(LOGIN_URL, data);
    if (!response.ok) {
        setError(true, "error_login")
    } else {
        setAuthCredentials(response.data.token, response.data.user_id, response.data.email, response.data.fullname)
        window.location.href = "../dashboard/index.html"
    }
}

function guestLogin() {
    setError(false, "error_login")
    logIn(GUEST_LOGIN)
}

function validateFullname(element) {
    const nameRegex = /^[a-zäöüß]+(?: [a-zäöüß]+){1,2}$/i;
    let valid = nameRegex.test(element.value.trim())
    setError(!valid, element.id + "_group")
    if (valid) {
        signUpValues.fullname = element.value.trim()
    }
}

function validateRegistrationEmail(element) {
    let valid = validateEmail(element)
    if (valid) {
        signUpValues.email = element.value.trim()
    }
}

function validatePW(element) {
    let valid = element.value.trim().length > 7;
    setError(!valid, element.id + "_group")

    if (valid) {
        signUpValues.password = element.value.trim()
    }

    let repeatedPwRef = document.getElementById("repeated_password")
    if (repeatedPwRef.value.trim().length > 0) {
        validateConfirmPW(repeatedPwRef)
    }
}

function validateConfirmPW(element) {
    let valid = document.getElementById("password").value.trim() == element.value.trim();
    setError(!valid, element.id + "_group")
    if (valid) {
        signUpValues.repeated_password = element.value.trim()
    }
}

function validatePrivacyCheckbox(element) {
    setError(!element.checked, element.id + "_group")
}

function validateLoginPW(element) {
    let valid = element.value.trim().length > 0;
    setError(!valid, element.id + "_group")
}

function validateEmail(element) {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    let valid = emailRegex.test(element.value.trim())
    setError(!valid, element.id + "_group")
    return valid;
}

function validateSignUp() {
    validateFullname(document.getElementById("fullname"))
    validateEmail(document.getElementById("email"))
    validatePW(document.getElementById("password"))
    validateConfirmPW(document.getElementById("repeated_password"))
    validatePrivacyCheckbox(document.getElementById("privacy_policy_checkbox"))

    const form = document.getElementById('sign_up_form');
    const elementWithErrorFalse = form.querySelector('[error="true"]');
    return elementWithErrorFalse == null
}