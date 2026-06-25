function getMemberListTemplate(currentBoard){
    let listHTML = "";
    for (let i = 0; i < currentBoard.members.length; i++) {
        if (i >= 4) {
            listHTML += `<li><div class="profile_circle  color_A">+${currentBoard.members.length - 4}</div></li>`
            break;
        }
        listHTML += `<li><div class="profile_circle  color_${getInitials(currentBoard.members[i].fullname)[0]}">${getInitials(currentBoard.members[i].fullname)}</div></li>`
    }
    return listHTML;
}

function getDetailTaskPersonTemplate(member){
    if (member) {
        return `<div class="profile_circle color_${getInitials(member.fullname)[0]}">${getInitials(member.fullname)}</div>
                            <p>${member.fullname}</p>`
    } else {
        return `<img src="../../assets/icons/face_icon.svg" alt="">
                            <p>unassigned</p>`
    }
}

function getSingleCommmentTemplate(comment) {
    let delete_btn = comment.author == getAuthFullname() ? `<img src="../../assets/icons/delete.svg" class="delete_btn" alt="" onclick="deleteComment(${comment.id})">` : ""
    let userInitials = getInitials(comment.author)
    return `        <article class="comment_wrapper d_flex_ss_gm w_full">
                        <div class="profile_circle color_${userInitials[0]}">${userInitials}</div>
                        <div class="d_flex_sc_gs f_d_c w_full">
                            <header class="d_flex_sc_gm w_full d_sb">
                                <div class="d_flex_sc_gm">
                                    <h4>${comment.author}</h4>
                                    <p>${timeDifference(comment.created_at)}</p>
                                </div>
                                ${delete_btn}
                            </header>
                            <p class="w_full">${comment.content}</p>
                        </div>    
                    </article>`
}

function getTaskCreateMemberListEntrieTemplate(type, currentBoard) {
    let listHtml = `<li onclick="unsetMemberAs('${type}'); toggleDropdown(this, event)">
                        <img src="../../assets/icons/face_icon.svg" alt="">
                        <p>unassigned</p>
                    </li>`
    currentBoard.members.forEach(member => {
        listHtml += `<li onclick="setMemberAs('${member.id}', '${type}'); toggleDropdown(this, event)">
                        <div class="profile_circle color_${getInitials(member.fullname)[0]}">${getInitials(member.fullname)}</div>
                        <p>${member.fullname}</p>
                    </li>`
    });

    return listHtml
}

function getBoardCardTemplate(task) {
    let assignee_html = task.assignee ?
        `<div class="profile_circle color_${getInitials(task.assignee.fullname)[0]}">${getInitials(task.assignee.fullname)}</div>` :
        `<img src="../../assets/icons/face_icon.svg" alt="">`
    return `            <li class="column_card" onclick="openTaskDetailDialog(${task.id})">
                            <header class="column_card_header">
                                <h4 class="font_white_color">${task.title}</h4>
                                <div class="d_flex_sc_gm">
                                    <img src="../../assets/icons/${task.priority}_prio_colored.svg" alt="">
                                    ${assignee_html}
                                </div>
                            </header>
                            <p class="column_card_content font_white_color">${task.description}</p>
                            ${getBoardCardMoveBtnTemplate(task)}
                        </li>`
}

function getBoardCardMoveBtnTemplate(task) {
    let statii = ['to-do', 'in-progress', 'review', 'done'];
    let currentStatusIndex = statii.indexOf(task.status);
    let moveBtns = "";
    if (currentStatusIndex > 0) {
        moveBtns += `<button onclick="modifyTaskStatus(${task.id}, '${statii[currentStatusIndex-1]}')">${statii[currentStatusIndex-1]}<img class="rotate_half" src="../../assets/icons/arrow_forward.svg" alt="" srcset=""></button>`
    }
    if (currentStatusIndex < statii.length - 1) {
        moveBtns += `<button onclick="modifyTaskStatus(${task.id}, '${statii[currentStatusIndex+1]}')">${statii[currentStatusIndex+1]} <img src="../../assets/icons/arrow_forward.svg" alt="" srcset=""></button>`
    }

    return `<div move-open="false" class="move_btn" onclick="toggleMoveOpen(this); stopProp(event)">
        <img src="../../assets/icons/swap_horiz.svg" alt="">
        <div class=" d_flex_sc_gs f_d_c pad_s">
            <p class="font_prime_color ">Move to</p>
            ${moveBtns}
        </div>
    </div>`
}