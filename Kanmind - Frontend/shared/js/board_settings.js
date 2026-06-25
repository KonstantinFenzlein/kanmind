let currentSettingsBoard

function validateBoardTitle(element){
    let valid = element.value.trim().length > 2 && element.value.trim().length < 64;
    setError(!valid, element.id + "_group")
    return valid
}

function validateMemberEmail(element, memberlist) {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    let valid = emailRegex.test(element.value.trim())
    let labelRef = document.getElementById("email_error_label")
    labelRef.innerText = "Please enter a valid email address."

    if(valid){
        valid = memberlist.filter( user => user.email == element.value.trim()).length == 0
        labelRef.innerText = "This email adress already exist as member."
    }
    
    setError(!valid, element.id + "_group")
    return valid 
}

async function openBoardSettingsDialog(id) {
    let board = await getBoardById(id);
    if (board) {
        currentSettingsBoard = board;
        document.getElementById("dialog_wrapper").setAttribute("current-dialog", "board_settings");
        toggleOpenId('dialog_wrapper');
        renderBoardSettingsDialog();
    } else {
        console.error("Board not found");
    }
}

async function getBoardById(id) {
    let response = await getData(BOARDS_URL + id + "/");
    if (response.ok) {
        return response.data;
    } else {
        return null;
    }
}

function renderBoardSettingsDialog(){
    document.getElementById("board_settings_title").innerText = currentSettingsBoard.title;
    renderBoardSettingsMemberList()
}

function renderBoardSettingsMemberList(){
    let htmltext = "";
    currentSettingsBoard.members.forEach(member => {
        if(member.id == currentSettingsBoard.owner_id){
            htmltext += `<li>${member.email} <p>(owner)</p></li>`
        } else {
            htmltext +=  `<li>${member.email}<button onclick="removeBoardSettingsMember(${member.id})" class="std_btn btn_prime ">Remove</button></li>`
        }
    });
    document.getElementById("board_settings_member_list").innerHTML = htmltext;
}

async function removeBoardSettingsMember(id){
    currentSettingsBoard.members = currentSettingsBoard.members.filter(member => member.id !== id);
    await patchBoardSettingsMembers()
    renderBoardSettingsMemberList();
}

function boardSettingsInviteMember(){
    let element = document.getElementById("board_settings_email_input")
    let valid = validateMemberEmail(element, currentSettingsBoard.members)
    if(valid){
        boardSettingsCheckMailAddress(element)
    }
}

async function boardSettingsCheckMailAddress(element){
    let mail = element.value.trim()
    let resp = await checkMailAddress(mail)
    if(resp){
        currentSettingsBoard.members.push(resp)
        renderBoardSettingsMemberList()
        document.getElementById("board_settings_email_input").value = "";
        await patchBoardSettingsMembers()
    } else {
        document.getElementById("email_error_label").innerText = "This email adress doesn't exist."
        setError(true, element.id + "_group")
    }
}


function patchBoardSettingsMembers(){
    let boardMemberIds = currentSettingsBoard.members.map(member => member.id)
    updateBoard({"members": boardMemberIds})
}


function toggleBoardTitleEdit(){
    let titleElement = document.getElementById("board_settings_title_group");
    let isEditing = titleElement.getAttribute("edit") === "true";
    titleElement.setAttribute("edit", !isEditing);
    if(!isEditing) {
        let inputElement = document.getElementById("board_settings_title_input");
        inputElement.value = currentSettingsBoard.title;
        inputElement.focus();
    }
}


async function setNewBoardTitle(){
    let inputElement = document.getElementById("board_settings_title_input");
    let title = inputElement.value.trim();
    if (validateBoardTitle(inputElement)) {
        
        let resp = await updateBoard({"title": title});
        if(resp.ok){
            currentSettingsBoard.title = title;
            let titleElement = document.getElementById("board_settings_title");
            titleElement.innerText = title;
            toggleBoardTitleEdit();
        }
        return true
    }
    return false
}

function openBoardDeleteToast(){
    let htmltext = `
            <article class="font_ d_flex_cc_gl">
                <div class=" d_flex_ss_gm f_d_c">
                    <h3>Delete Board</h3>
                    <p>Are you sure you want to delete the board ${currentSettingsBoard.title}?</p>
                </div>
                <div class="font_sec_color d_flex_cc_gm f_d_c">
                    <button onclick="deleteBoard()" class="std_btn btn_prime d_flex_sc_gs">
                        <img src="../../assets/icons/delete_dark.svg" alt="">
                        <p>Delete Board</p>
                    </button>
                    <button onclick="deleteLastingToast()" class="font_prime_color std_btn toast_cancel d_flex_sc_gs">
                        <p class="w_full">Cancel</p>
                    </button>
                </div>
            </article>`
    showToastLastingMessage(true, htmltext)
}