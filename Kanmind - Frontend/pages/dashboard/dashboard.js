let currentAssignedTickets = [];
let currentReviewerTickets = [];
let currentBoards = [];
let currenTaskFilter = "assigned"
let isLoadingTasks = false;



async function init(){
    await setDashboardData();
    renderDashboard();
}

async function setDashboardData(){
    await getBoards();
    await getAssignedTasks();
}

async function getBoards() {
    let boardsResp = await getData(BOARDS_URL);

    if (boardsResp.ok) {
        currentBoards = boardsResp.data;
    } else {
        console.warn("BOARDS_URL loadingerror")
    }
}

async function getAssignedTasks() {
    let tasksResp = await getData(TASKS_ASSIGNED_URL);

    if (tasksResp.ok) {
        currentAssignedTickets = tasksResp.data;
    } else {
        console.warn("TASKS_ASSIGNED_URL loadingerror")
    }
}

async function getReviewerTasks() {
    let tasksResp = await getData(TASKS_REVIEWER_URL);

    if (tasksResp.ok) {
        currentReviewerTickets = tasksResp.data;
    } else {
        console.warn("TASKS_REVIEWER_URL loadingerror")
    }
}

function renderDashboard(){
    renderWelcomeMessage();
    renderUrgentTask()
    let progress = currentAssignedTickets.filter(task => task.status == "done" ).length / currentAssignedTickets.length * 100;
    drawWaveChart(progress); 
    drawPieChart(currentAssignedTickets);
    renderBoardList();
    renderMemberAndTaskCount();
    renderTaskList();
}

function renderWelcomeMessage(){
    let user = getAuthUser();
    document.getElementById('welcome_message').innerHTML = `<img src="../../assets/icons/shake_hands.png" alt=""><span class="font_white_color"> Welcome </span>${user.fullname}!`
}

function renderBoardList(){
    let htmlText = "";
    currentBoards.forEach(board => {
        htmlText += `<li><a class="link" href="../../pages/board/?id=${board.id}">${board.title}</a></li>`
    });
    if(currentBoards.length <= 0){
        htmlText = `<h3 class="font_prime_color">No boards available</h3>`
    }
    document.getElementById('dashboard_boardlist').innerHTML = htmlText;
}

async function toggleTicketsTypeSwitch(element){
    if(!isLoadingTasks){
        toggleSwitch(element)
        isLoadingTasks = true;
        if(currenTaskFilter == "review"){
            currenTaskFilter = "assignee"
        } else {
            currenTaskFilter = "review"
        }
        await renderTaskList()
        isLoadingTasks = false;
    }
}

async function renderTaskList(){
    let renderList = []
    if(currenTaskFilter == "review"){
        await getReviewerTasks()
        renderList = currentReviewerTickets
    } else {
        await getAssignedTasks()
        renderList = currentAssignedTickets
    }

    document.getElementById('dashboard_tasklist').innerHTML = getTaskListTemplate(renderList);
}

function getTaskListTemplate(renderList){
    let htmlText = "";
    renderList.forEach(task => {
        htmlText += getSingleTaskTemplate(task)
    });
    if(renderList.length <= 0){
        htmlText = `<h3 class="font_prime_color">No tasks available</h3>`
    }
    return htmlText;
}

function getSingleTaskTemplate(task) {
    let assigneeTemplate = task.assignee ? 
        `<div class="profile_circle color_${getInitials(task.assignee.fullname)[0]}">${getInitials(task.assignee.fullname)}</div>` : 
        `<img src="../../assets/icons/face_icon.svg" alt="">`

    return `        <tr onclick="redirectToBoardWTask(${task.id})">
                        <td class="title">${task.title}</td>
                        <td class="ws_nw">${task.due_date}</td>
                        <td>
                            <div class="priority-badge" priority="${task.priority}"></div>
                        </td>
                        <td class="ws_nw">${task.status}</td>
                        <td class="d_flex_cc_gs task_count" zero="${task.comments_count==0}"> 
                            <p class="font_sec_color">${task.comments_count}</p> 
                            <img src="../../assets/icons/comment_bubble_filled.svg" alt="" srcset="">
                            <img src="../../assets/icons/comment_bubble_empty.svg" alt="" srcset="">
                        </td>
                        <td>
                            ${assigneeTemplate}
                        </td>
                    </tr>`
}

function redirectToBoardWTask(taskId){
    let taskList = currenTaskFilter == "review" ? currentReviewerTickets : currentAssignedTickets;
    let task = taskList.find(task => task.id == taskId);
    if(task) {
        window.location.href = `../../pages/board/?id=${task.board}&task_id=${task.id}`;
    }
}

function renderMemberAndTaskCount(){
    let userId = getAuthUserId()
    document.getElementById('dashboard_task_count').innerText = currentAssignedTickets.length;
    document.getElementById('dashboard_member_count').innerText = currentBoards.filter(board => board.owner_id != userId).length;
}

function renderUrgentTask(){
    let task = getNearestDueDateTask();
    let count = currentAssignedTickets.filter(task => task.priority == "high").length;
    document.getElementById('high_prio_count').innerText = count
    document.getElementById('upcoming_deadline').innerText = task ? formatDate(task.due_date) : "no upcoming deadline";
}

function getNearestDueDateTask() {
    const today = new Date();
    let nearestTask = null;
    let minDiff = Infinity;

    currentAssignedTickets.forEach(task => {
        const dueDate = new Date(task.due_date);
        const diff = dueDate - today;

        if (diff >= 0 && diff < minDiff) {
            minDiff = diff;
            nearestTask = task;
        }
    });

    return nearestTask;
}

function formatDate(isoDate) {
    const date = new Date(isoDate);
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

function redirectToBoards(){
    window.location.href = "../../pages/boards/"
}
