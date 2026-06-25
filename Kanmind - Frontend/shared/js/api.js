function setAuthCredentials(token, userId, email, fullname) {
    localStorage.setItem('auth-token', token);
    localStorage.setItem('auth-user-id', userId);
    localStorage.setItem('auth-email', email);
    localStorage.setItem('auth-fullname', fullname);
}

function removeAuthCredentials() {
    localStorage.removeItem('auth-token');
    localStorage.removeItem('auth-user-id');
    localStorage.removeItem('auth-email');
    localStorage.removeItem('auth-fullname');
}

function getAuthToken() {
    return localStorage.getItem('auth-token');
}

function getAuthUserId() {
    return localStorage.getItem('auth-user-id');
}

function getAuthEmail() {
    return localStorage.getItem('auth-email');
}

function getAuthFullname() {
    return localStorage.getItem('auth-fullname');
}

function getAuthUser(){
    let fullname = getAuthFullname();
    let user = {
        "id": getAuthUserId(),
        "initials": getInitials(fullname),
        "fullname": fullname,
        "email":getAuthEmail()
    }
    return user
}

async function checkMailAddress(mail){
    // let mailResp = await getData(`${MAIL_CHECK_URL}?email=${encodeURIComponent(mail)}`);
    let mailResp = await getData(`${MAIL_CHECK_URL}?email=${mail}`);
    if (mailResp.ok) {
        return mailResp.data;
    } else {
        return false
    }
}

function createHeaders() {
    const headers = {};

    const token = getAuthToken();
    if (token) {
        headers['Authorization'] = `Token ${token}`;
    }

    return headers;
}

function getErrorMessage(error) {
    let errorMessage = 'Network error';

    if (error instanceof TypeError) {
        errorMessage = 'There was an issue with the request or network connection.';
    } else if (error instanceof SyntaxError) {
        errorMessage = 'Response was not valid JSON.';
    } else if (error.message.includes('Failed to fetch')) {
        errorMessage = 'Failed to connect to the server.';
    }

    return errorMessage;
}

function getFormData(form){
    const formData = new FormData(form);
    return Object.fromEntries(formData.entries());
}

async function getData(endpoint) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'GET',
            headers: createHeaders(),
        });
        const responseData = await response.json();
        return {
            ok: response.ok,
            status: response.status,
            data: responseData
        };

    } catch (error) {
        const errorMessage = getErrorMessage(error);
        return {
            ok:false,
            status: 'error',
            message: errorMessage
        };
    }
}

async function postData(endpoint, data) {
    
    let header = createHeaders();
    header['Content-Type'] = 'application/json';
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: header,
            body: JSON.stringify(data)
        });
        
        const responseData = await response.json();
        return {
            ok: response.ok,
            status: response.status,
            data: responseData
        };
        
    } catch (error) {
        const errorMessage = getErrorMessage(error);
        return {
            ok:false,
            status: 'error',
            message: errorMessage
        };
    }
}


async function patchData(endpoint, data) {
    let header = createHeaders();
    header['Content-Type'] = 'application/json';
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'PATCH',
            headers: header,
            body: JSON.stringify(data)
        });

        const responseData = await response.json();
        return {
            ok: response.ok,
            status: response.status,
            data: responseData
        };

    } catch (error) {
        const errorMessage = getErrorMessage(error);
        return {
            ok:false,
            status: 'error',
            message: errorMessage
        };
    }
}

async function deleteData(endpoint) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'DELETE',
            headers: createHeaders(),
        });
        let responseData = null;
        if (response.status !== 204) {
            responseData = await response.json();
        }
        return {
            ok: response.ok,
            status: response.status,
            data: responseData
        };

    } catch (error) {
        const errorMessage = getErrorMessage(error);
        return {
            ok:false,
            status: 'error',
            message: errorMessage
        };
    }
}