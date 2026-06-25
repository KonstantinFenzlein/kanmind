let currentCreateBoard = {
    "title" : "",
    "members":[]
}



let boardList = []

function redirectToBoard(id){
    window.location.href = "../../pages/board/?id="+id
}

async function getAndRenderBoardList(){
    boardList = await getBoards()
    if(boardList){
        renderBoardList()
    }
}

async function getBoards(){
    let boardResp = await getData(BOARDS_URL);

    if (boardResp.ok) {
        return boardResp.data;
    } else {
        return null
    }
}

function openBoardCreateDialog(){
    toggleOpenId('dialog_wrapper')
    document.getElementById("dialog_wrapper").setAttribute("current-dialog", "board_create");
    currentCreateBoard = {
        "title" : "",
        "members":[]
    }
    renderCreateDialogMemberList()
    document.getElementById("board_title_input").value = "";
}

async function boardCreateInviteMember(){
    let element = document.getElementById("create_board_email_input")
    let valid = validateMemberEmail(element, currentCreateBoard.members)
    if(valid){
        boardCreateCheckMailAddress(element)
    }
}

function resetMailError(){
    setError(false, "create_board_email_input_group")
}



async function boardCreateCheckMailAddress(element){
    let mail = element.value.trim()
    let resp = await checkMailAddress(mail)
    if(resp){
        currentCreateBoard.members.push(resp)
        renderCreateDialogMemberList()
        document.getElementById("create_board_email_input").value = "";
    } else {
        document.getElementById("email_error_label").innerText = "This email adress doesn't exist."
        setError(true, element.id + "_group")
    }
}



async function boardCreateSubmit(event) {
    event.preventDefault();
    let element = document.getElementById("board_title_input")
    if(validateBoardTitle(element)){
        currentCreateBoard.title = element.value.trim()
        await createBoard()
    }
}

async function createBoard(){
    let boardMemberIds = currentCreateBoard.members.map(member => member.id)
    let response = await postData(BOARDS_URL, {"title": currentCreateBoard.title, "members": boardMemberIds});
    if (!response.ok) {
        let errorArr = extractErrorMessages(response.data)
        showToastMessage(true, errorArr)
    } else {
        toggleOpenId('dialog_wrapper');
        await getAndRenderBoardList();
    }
}

function cancelCreateBoard(){
    currentCreateBoard = {
        "title" : "",
        "members":[]
    }
    toggleOpenId('dialog_wrapper')
}

function renderCreateDialogMemberList(){
    let htmltext = "";
    currentCreateBoard.members.forEach(member => {
        htmltext +=  `<li>${member.email}<button onclick="removeCurrentMember(${member.id})" class="std_btn btn_prime">Remove</button></li>`
    });
    document.getElementById("create_board_member_list").innerHTML = htmltext;
}

function removeCurrentMember(id){
    currentCreateBoard.members = currentCreateBoard.members.splice(id, 1);
    renderCreateDialogMemberList();
}

function renderBoardList(){
    let htmltext = "";
    let searchValue = document.getElementById("board_search").value.trim().toLowerCase();
    let renderBoardList = boardList.filter(board => board.title.toLowerCase().includes(searchValue));
    renderBoardList.forEach(board => {
        htmltext += getBoardlistEntrieTemplate(board);
    });
    if(renderBoardList.length <= 0){
        htmltext = `<h3 class="font_prime_color">...No boards available...</h3>`
    }
    document.getElementById("board_list").innerHTML = htmltext;
}

function getBoardlistEntrieTemplate(board){
    return `    <li class="card d_flex_sc_gl w_full" onclick="redirectToBoard(${board.id})">
                    <h3>${board.title}</h3>
                    <div class="board_list_entry_part d_flex_sc_gs">
                        <img src="../../assets/icons/member_icon.svg" alt="">
                        <p class="fs_m">${board.member_count}</p>
                        <p>Members</p>
                    </div>
                    <div class="board_list_entry_part d_flex_sc_gs">
                        <img src="../../assets/icons/ticket_icon.svg" alt="">
                        <p class="fs_m">${board.ticket_count}</p>
                        <p>Tickets</p>
                    </div>
                    <div class="board_list_entry_part d_flex_sc_gs">
                        <img src="../../assets/icons/assign_icon.svg" alt="">
                        <p class="fs_m">${board.tasks_to_do_count}</p>
                        <p>Tasks To-do</p>
                    </div>
                    <div class="board_list_entry_part d_flex_sc_gs">
                        <div class="priority-badge" priority="high"></div>
                        <p class="fs_m">${board.tasks_high_prio_count}</p>
                        <p>High Prio</p>
                    </div>
                    <button onclick="openBoardSettingsDialog(${board.id}); stopProp(event)" class="std_btn d_flex_sc_gs board_settings_btn">
                        <img src="../../assets/icons/settings.svg" alt="">
                    </button>
                </li>`
}

async function updateBoard(data){
    let response = await patchData(BOARDS_URL + currentSettingsBoard.id + "/", data);
    if (!response.ok) {
        let errorArr = extractErrorMessages(response.data)
        showToastMessage(true, errorArr)
    } else {
        await getAndRenderBoardList();
    }
    return response;
}


async function deleteBoard(){
    await deleteData(BOARDS_URL + currentSettingsBoard.id + "/");
    toggleOpenId('dialog_wrapper');
    getAndRenderBoardList();
    deleteLastingToast()
}
