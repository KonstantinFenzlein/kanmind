function drawPieChart(currentAssignedTickets) {
    let ticketData = getPieChartData(currentAssignedTickets)
    let labels = ['To-do', 'In progress', 'Review', 'Done'];

    if (ticketData.every(val => val === 0)) {
        ticketData = [1];
        labels = ['No tasks assigned'];
    }

    const ctx = document.getElementById('ticketsChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: ticketData,
                backgroundColor: ['#8E44AD', '#F1C40F', '#E67E22', '#3498DB'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: 'white',
                        usePointStyle: true,
                        pointStlye: 'circle',
                    }
                }
            }
        }
    });
};

function getPieChartData(currentAssignedTickets) {
    return [
        currentAssignedTickets.filter(task => task.status == "to-do").length,
        currentAssignedTickets.filter(task => task.status == "in-progress").length,
        currentAssignedTickets.filter(task => task.status == "review").length,
        currentAssignedTickets.filter(task => task.status == "done").length,
    ]
}

function drawWaveChart(progress) {
    let progressIsValid = true;
    if (progress < 0 || progress > 100 || isNaN(progress)) {
        progress = 0;
        progressIsValid = false;
    }
    const ctx = document.getElementById("waveChart").getContext("2d");
    const wavePlugin = {
        id: 'waveProgress',
        beforeDraw(chart) {
            const { ctx, chartArea: { left, right, top, bottom }, scales: { x } } = chart;
            const width = right - left;
            const height = bottom - top;
            const progressX = left + (width * (progress / 100));

            ctx.save();

            // Wave strokes
            function drawWave(color, startX, endX) {
                ctx.beginPath();
                ctx.moveTo(startX, bottom - height / 2);
                const waveLength = 90;  // Wavelength
                const amplitude = 10;   // Wavehight

                for (let x = startX; x <= endX; x += 2) {
                    const y = bottom - height / 2 + Math.sin((x / waveLength) * Math.PI * 2) * amplitude;
                    ctx.lineTo(x, y);
                }

                ctx.lineWidth = 8;
                ctx.strokeStyle = color;
                ctx.stroke();
            }

            drawWave("#FFD700", left, progressX);
            drawWave("#345678", progressX, right);

            // Progress Text - Currently aligned in center
            ctx.fillStyle = "#FFD700";
            ctx.font = "16px Arial";
            ctx.textAlign = "center";
            let text = progressIsValid ? progress.toFixed(2) + "%" : "No Tasks found";
            ctx.fillText(text, left + width / 2, bottom - height / 2 - 20);

            // Numbers left and right
            ctx.fillStyle = "#ffffff";
            ctx.font = "14px Arial";
            ctx.textAlign = "left";
            ctx.fillText("0", left, bottom);
            ctx.textAlign = "right";
            ctx.fillText("100", right, bottom);

            ctx.restore();
        }
    };

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Fortschritt"],
            datasets: [{
                label: "Tasks Resolved",
                data: [progress],
                backgroundColor: "rgba(0, 0, 0, 0)",
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            height: 100,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { display: false },
                y: { display: false }
            }
        },
        plugins: [wavePlugin]
    });
    ;
}