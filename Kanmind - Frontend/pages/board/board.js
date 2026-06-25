let currentBoard = {}
let currentTask
let currentComments
let isShiftPressed = false
let currentMemberList

function setShift(event) {
    if (event.keyCode == 16) isShiftPressed = true
}

function unsetShift(event) {
    if (event.keyCode == 16) isShiftPressed = false
}

function cleanCurrentTask() {
    currentTask = {
        "id": null,
        "title": null,
        "description": null,
        "status": null,
        "priority": 'medium',
        "assignee": null,
        "reviewer": null,
        "due_date": null
    }
}

async function init() {
    await setBoard();
    cleanCurrentTask();
    renderAllTasks();
    renderMemberList();
    renderTitle();
    if(getParamFromUrl("task_id")) openTaskDetailDialog(getParamFromUrl("task_id"));
        
}

function renderTitle(){
    document.getElementById('board_title_link').innerText = currentBoard.title;
    document.getElementById('board_title').innerText = currentBoard.title;
}

async function setBoard(){
    let boardResp = await getData(BOARDS_URL + getParamFromUrl("id"));
    if (boardResp.ok) {
        currentBoard = boardResp.data;
    } 
}


function renderMemberList() {
    let listRef = document.getElementById('short_profile_list');
    listRef.innerHTML = getMemberListTemplate(currentBoard);
}

async function openTaskDetailDialog(id) {
    currentTask = JSON.parse(JSON.stringify(getTaskById(id)));
    changeCurrentDialog("task_detail_dialog");
    toggleOpenId('dialog_wrapper');
    await loadAndRenderDetailTask(id);
}

async function loadAndRenderDetailTask(id) {
    currentComments = await getTaskComments(id)
    renderDetailTask()
}

function renderDetailTask() {
    document.getElementById('task_detail_dialog_select').value = currentTask.status;
    document.getElementById('detail_task_title').innerHTML = currentTask.title
    document.getElementById('detail_task_description').innerHTML = currentTask.description
    document.getElementById('detail_task_assignee').innerHTML = getDetailTaskPersonTemplate(currentTask.assignee)
    document.getElementById('detail_task_reviewer').innerHTML = getDetailTaskPersonTemplate(currentTask.reviewer)
    renderDetailTaskDueDate()
    renderDetailTaskPriority()
    renderDetailTaskComments()
}

function renderDetailTaskPriority(){
    let prioRef = document.getElementById('detail_task_priority');
    prioRef.innerHTML =  `<div priority="${currentTask.priority}" class="priority-badge"></div><p >${currentTask.priority}</p>`
}

function renderDetailTaskDueDate(){
    let prioRef = document.getElementById('detail_task_due_date');
    prioRef.innerHTML =  currentTask.due_date
}

async function getTaskComments(id) {
    let commentResp = await getData(TASKS_URL + id + "/comments/");
    if (commentResp.ok) {
        return commentResp.data;
    } else {
        return []
    }
}

async function sendComment(event, element) {
    if (event.keyCode == 13 && !isShiftPressed) {
        postComment(element)
    }
}

async function sendCommentDirectly(){
    let element = document.getElementById('comment_textarea')
    postComment(element)
}

async function postComment(element){
    let newComment = {
        "content": element.value.trim()
    }
    if (newComment.content.length > 0) {
        let response = await postData(TASKS_URL + currentTask.id + "/comments/", newComment);
        if (!response.ok) {
            let errorArr = extractErrorMessages(response.data)
            showToastMessage(true, errorArr)
        } else {
            element.value = '';
            currentComments = await getTaskComments(currentTask.id);
            renderDetailTaskComments()
        }
    }
}

function renderDetailTaskComments() {
    let userInitials = getInitials(getAuthFullname())
    document.getElementById('comment_sender_profile').innerHTML = `<div class="profile_circle color_${userInitials[0]}">${userInitials}</div>`;
    let listRef = document.getElementById("task_comment_list")
    let listHtml = "";
    currentComments.forEach(comment => {
        listHtml += getSingleCommmentTemplate(comment)
    });
    listRef.innerHTML = listHtml;
}

function openCreateTaskDialog(status) {
    cleanCurrentTask()
    if (status) {
        currentTask.status = status;
    } else {
        currentTask.status = "to-do";
    }
    changeCurrentDialog("create_edit_task_dialog")
    toggleOpenId('dialog_wrapper')
    fillEditCreateTaskDialog('create')
}

function openEditTaskDialog() {
    changeCurrentDialog("create_edit_task_dialog")

    fillEditCreateTaskDialog('edit')
}

function deleteCurrentTask() {
    deleteTask(currentTask.id)
}

function deleteComment(id) {
    deleteData(TASKS_URL + currentTask.id + "/comments/" + id + "/").then(async response => {
        if (!response.ok) {
            let errorArr = extractErrorMessages(response.data)
            showToastMessage(true, errorArr)
        } else {
            currentComments = await getTaskComments(currentTask.id);
            renderDetailTaskComments()
        }
    })
}

function deleteTask(id) {
    deleteData(TASKS_URL + id + "/").then(async response => {
        if (!response.ok) {
            let errorArr = extractErrorMessages(response.data)
            showToastMessage(true, errorArr)
        } else {
            cleanCurrentTask()
            toggleOpenId('dialog_wrapper')
            await loadAndRenderTasks()
        }
    })
}

function fillEditCreateTaskDialog(type) {
    document.getElementById("create_edit_task_dialog").setAttribute('dialog-type', type);
    fillCreateEditTaskTitleInputDesc()
    renderTaskCreateMemberList()
    setTaskCreateDropdownPrioHeader()
    setSelectAddEditTaskStatusDropdown()
}

function renderTaskCreateMemberList() {
    document.getElementById("create_edit_task_assignee").innerHTML = getTaskCreateMemberListEntrieTemplate("assignee", currentBoard)
    document.getElementById("create_edit_task_reviewer").innerHTML = getTaskCreateMemberListEntrieTemplate("reviewer", currentBoard)
    setTaskCreateDropdownHeader('assignee')
    setTaskCreateDropdownHeader('reviewer')
}

function setTaskCreateDropdownHeader(type) {
    let headRef = document.getElementById(`create_edit_task_${type}_head`)
    if (currentTask[type]) {
        let initials = getInitials(currentTask[type].fullname)
        headRef.innerHTML = `<div class="profile_circle color_${initials[0]}">${initials}</div><p>${currentTask[type].fullname}</p>`
    } else {
        headRef.innerHTML = `<img src="../../assets/icons/face_icon.svg" alt=""><p>unassigned</p>`
    }
}

function unsetMemberAs(type) {
    currentTask[type] = null
    setTaskCreateDropdownHeader(type)
}

function setMemberAs(memberId, type) {
    currentTask[type] = getMemberById(memberId)
    setTaskCreateDropdownHeader(type)
}

function getMemberById(id) {
    return currentBoard.members.find(member => member.id == id)
}

function getTaskById(id) {
    return currentBoard.tasks.find(task => task.id == id)
}

function setTaskCreatePrio(prio) {
    currentTask.priority = prio;
    setTaskCreateDropdownPrioHeader();
}

function setTaskCreateDropdownPrioHeader() {
    let headerRef = document.getElementById('create_edit_task_prio_head');
    headerRef.innerHTML = `<div class="priority-badge" priority="${currentTask.priority}"></div><p>${currentTask.priority}</p>`
}

function setTaskCreateDate(element) {
    currentTask.due_date = element.value;
}

function changeCurrentDialog(currentDialog) {
    const dialogs = document.querySelectorAll('[current_dialog]');
    dialogs.forEach(dialog => {
        dialog.setAttribute('current_dialog', 'false');
    });
    document.getElementById(currentDialog).setAttribute('current_dialog', 'true');
}

function validateCreateEditTaskTitle(element) {
    let valid = element.value.trim().length > 2;
    setError(!valid, element.id + "_group")
    return valid
}

function validateCreateEditTaskDueDate(element) {
    let valid = element.value.trim().length > 0;
    setError(!valid, element.id + "_group")
    return valid
}

async function submitCreateTask(event) {
    event.preventDefault();
    let newTask = getValidatedTask()
    if (newTask) {
        await createTask(newTask)
    }
}

function getValidatedTask(){
    let titleRef = document.getElementById('create_edit_task_title_input');
    let dateRef = document.getElementById('create_edit_task_date_input');
    if (validateCreateEditTaskTitle(titleRef) && validateCreateEditTaskDueDate(dateRef)) {
        let updatedTask = {
            "board": currentBoard.id,
            "title": titleRef.value,
            "description": document.getElementById('create_edit_task_description').value,
            "status": currentTask.status,
            "priority": currentTask.priority,
            "reviewer_id": currentTask.reviewer ? currentTask.reviewer.id : null,
            "assignee_id": currentTask.assignee ? currentTask.assignee.id : null,
            "due_date": dateRef.value
        }
        return updatedTask
    }
    return false
}

async function submitEditTask() {
    let updatedTask = getValidatedTask()
    if (updatedTask) {
        await editTask(updatedTask, currentTask.id)
    }
}

async function editTask(updatedTask, id) {
    let response = await patchData(TASKS_URL + id + "/", updatedTask);
    if (!response.ok) {
        let errorArr = extractErrorMessages(response.data)
        showToastMessage(true, errorArr)
    } else {
        cleanCurrentTask()
        toggleOpenId('dialog_wrapper')
        await loadAndRenderTasks()
    }
}

async function createTask(newTask) {
    let response = await postData(TASKS_URL, newTask);
    if (!response.ok) {
        let errorArr = extractErrorMessages(response.data)
        showToastMessage(true, errorArr)
    } else {
        cleanCurrentTask()
        toggleOpenId('dialog_wrapper')
        await loadAndRenderTasks()
    }
}

function setSelectAddEditTaskStatusDropdown() {
    document.getElementById('create_edit_task_dialog_select').value = currentTask.status;
}

function modifyAddEditTaskStatusDropdown(){
    let status = document.getElementById('create_edit_task_dialog_select').value
    currentTask.status = status;
}

async function modifyTaskStatusDropdown(){
    let status = document.getElementById('task_detail_dialog_select').value
    await modifyTaskStatus(currentTask.id, status)
}

async function modifyTaskStatus(id, status) {
    let response = await patchData(TASKS_URL + id + "/", {"status": status});
    if (!response.ok) {
        let errorArr = extractErrorMessages(response.data)
        showToastMessage(true, errorArr)
    } else {
        await loadAndRenderTasks()
    }
}
function toggleMoveOpen(element) {
    resetAllMoveOpen()
    let isOpen = element.getAttribute('move-open') === 'true';
    element.setAttribute('move-open', !isOpen);
}

function resetAllMoveOpen() {
    document.querySelectorAll('.move_btn').forEach(btn => btn.setAttribute('move-open', 'false'));
}

function abbortCreateEditTask() {
    cleanCurrentTask()
    fillCreateEditTaskTitleInputDesc()
    toggleOpenId('dialog_wrapper')
}

function fillCreateEditTaskTitleInputDesc() {
    document.getElementById('create_edit_task_title_input').value = currentTask.title;
    document.getElementById('create_edit_task_date_input').value = currentTask.due_date;
    document.getElementById('create_edit_task_description').value = currentTask.description;
}

async function loadAndRenderTasks() {
    await setBoard();
    renderAllTasks()
}

function renderAllTasks() {
    let searchRef = document.getElementById('searchbar_tasks')
    let taskList = []
    if (searchRef.value.length > 0) {
        taskList = searchInTasks(searchRef.value)
    } else {
        taskList = currentBoard.tasks
    }
    let statii = ['to-do', 'in-progress', 'review', 'done']
    statii.forEach(status => {
        let filteredList = taskList.filter(task => task.status == status)
        renderSingleColumn(status, filteredList)
    });
}

function renderSingleColumn(status, filteredList) {
    document.getElementById(`${status}_column`).innerHTML = "";
    filteredList.forEach(task => {
        document.getElementById(`${status}_column`).innerHTML += getBoardCardTemplate(task);
    });
}

function searchInTasks(searchTerm) {
    const lowerCaseSearch = searchTerm.toLowerCase();

    return currentBoard.tasks.filter(task => {
        const titleMatch = task.title?.toLowerCase().includes(lowerCaseSearch);
        const descriptionMatch = task.description?.toLowerCase().includes(lowerCaseSearch);
        return titleMatch || descriptionMatch;
    });
}

async function updateBoard(data){
    let response = await patchData(BOARDS_URL + currentSettingsBoard.id + "/", data);
    if (!response.ok) {
        let errorArr = extractErrorMessages(response.data)
        showToastMessage(true, errorArr)
    } else {
        currentBoard.title = response.data.title;
        renderTitle()
        
    }
    return response;
}

async function deleteBoard(){
    let response = await deleteData(BOARDS_URL + currentSettingsBoard.id + "/");
    if(response.ok){
        window.location.href = "../../pages/boards/"
    } else {
        let errorArr = extractErrorMessages(response.data)
        showToastMessage(true, errorArr)
    }
    deleteLastingToast() 
}

function triggerDateInput(element) {
    document.getElementById(element).nextElementSibling.showPicker();
}

async function openEditBoardDialog() {
    document.getElementById("edit_board_dialog").setAttribute("current_dialog", "true");
    openBoardSettingsDialog(currentBoard.id)
}