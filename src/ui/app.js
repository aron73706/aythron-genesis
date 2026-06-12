// Aythron Genesis Frontend Client Logic

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const providerSelect = document.getElementById("provider-select");
    const ollamaHostGroup = document.getElementById("ollama-host-group");
    const ollamaModelGroup = document.getElementById("ollama-model-group");
    const ollamaHostInput = document.getElementById("ollama-host");
    const ollamaModelInput = document.getElementById("ollama-model");
    const saveConfigBtn = document.getElementById("save-config-btn");
    
    const goalInput = document.getElementById("goal-input");
    const runGoalBtn = document.getElementById("run-goal-btn");
    const runSpinner = document.getElementById("run-spinner");
    
    const systemStatusBadge = document.getElementById("system-status-badge");
    const systemStatusText = document.getElementById("system-status-text");
    const activeProviderText = document.getElementById("active-provider-text");
    
    // Agent nodes
    const nodeManager = document.getElementById("node-manager");
    const nodePlanner = document.getElementById("node-planner");
    const nodeWorker = document.getElementById("node-worker");
    const nodeReviewer = document.getElementById("node-reviewer");
    
    // Links
    const linkMtoP = document.querySelector(".link-m-to-p");
    const linkPtoW = document.querySelector(".link-p-to-w");
    const linkWtoR = document.querySelector(".link-w-to-r");
    
    // Task board
    const tasksListContainer = document.getElementById("tasks-list-container");
    
    // Memory Editor
    const tabButtons = document.querySelectorAll(".tab-btn");
    const memoryEditor = document.getElementById("memory-editor");
    const saveMemoryBtn = document.getElementById("save-memory-btn");
    const editorStatusText = document.getElementById("editor-status-text");
    
    // Terminal Console
    const terminalLogs = document.getElementById("terminal-logs");
    const clearLogsBtn = document.getElementById("clear-logs-btn");

    // Local state
    let activeTab = "project_state.json";
    let isRunning = false;
    let logLineCount = 0;
    let memoryData = {};
    let pollInterval = null;

    // Toggle Ollama fields
    providerSelect.addEventListener("change", () => {
        if (providerSelect.value === "ollama") {
            ollamaHostGroup.style.display = "flex";
            ollamaModelGroup.style.display = "flex";
        } else {
            ollamaHostGroup.style.display = "none";
            ollamaModelGroup.style.display = "none";
        }
    });

    // Save configuration
    saveConfigBtn.addEventListener("click", async () => {
        const payload = {
            provider_type: providerSelect.value,
            ollama_host: ollamaHostInput.value,
            default_model: ollamaModelInput.value
        };
        try {
            const res = await fetch("/api/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.status === "success") {
                updateProviderBadge(data.config.provider_type, data.config.default_model);
                appendLog("[SYSTEM] Configuration updated successfully.");
            } else {
                alert("Failed to update config");
            }
        } catch (e) {
            console.error(e);
            appendLog(`[ERROR] Failed to save config: ${e.message}`, "error-line");
        }
    });

    // Run goal
    runGoalBtn.addEventListener("click", async () => {
        const goal = goalInput.value.trim();
        if (!goal) {
            alert("Please specify a goal objective.");
            return;
        }

        try {
            const res = await fetch("/api/goals", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ goal: goal })
            });
            const data = await res.json();
            if (res.status === 200) {
                appendLog(`[SYSTEM] Starting execution run for goal: "${goal}"`);
                isRunning = true;
                updateUIRunningState(true);
            } else {
                appendLog(`[ERROR] Failed to start run: ${data.detail}`, "error-line");
            }
        } catch (e) {
            console.error(e);
            appendLog(`[ERROR] Error starting execution: ${e.message}`, "error-line");
        }
    });

    // Clear console output
    clearLogsBtn.addEventListener("click", () => {
        terminalLogs.innerHTML = "";
        logLineCount = 0;
    });

    // Tab buttons for memory files
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            activeTab = btn.getAttribute("data-tab");
            renderTabContent();
        });
    });

    // Save edited memory markdown files
    saveMemoryBtn.addEventListener("click", async () => {
        const content = memoryEditor.value;
        try {
            saveMemoryBtn.disabled = true;
            saveMemoryBtn.textContent = "Saving...";
            const res = await fetch("/api/memory/write", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename: activeTab, content: content })
            });
            const data = await res.json();
            if (res.status === 200) {
                editorStatusText.textContent = "Changes saved successfully!";
                setTimeout(() => {
                    editorStatusText.textContent = "Editable Mode";
                }, 3000);
                // Refresh memory data
                fetchMemoryData();
            } else {
                alert(`Error saving memory: ${data.detail}`);
            }
        } catch (e) {
            alert(`Network error saving memory: ${e.message}`);
        } finally {
            saveMemoryBtn.disabled = false;
            saveMemoryBtn.textContent = "Save Changes";
        }
    });

    // Helper functions
    function updateProviderBadge(provider, model) {
        if (provider === "ollama") {
            activeProviderText.textContent = `Ollama (${model})`;
        } else {
            activeProviderText.textContent = "Sandbox Mode";
        }
    }

    function updateUIRunningState(running) {
        if (running) {
            runSpinner.style.display = "block";
            runGoalBtn.disabled = true;
            goalInput.disabled = true;
            systemStatusBadge.classList.add("active");
            systemStatusText.textContent = "Executing";
        } else {
            runSpinner.style.display = "none";
            runGoalBtn.disabled = false;
            goalInput.disabled = false;
            systemStatusBadge.classList.remove("active");
            systemStatusText.textContent = "Idle";
        }
    }

    function appendLog(text, className = "system-line") {
        const line = document.createElement("div");
        line.className = `log-line ${className}`;
        line.textContent = text;
        terminalLogs.appendChild(line);
        terminalLogs.scrollTop = terminalLogs.scrollHeight;
    }

    // Fetches runtime config initially
    async function fetchInitialConfig() {
        try {
            const res = await fetch("/api/config");
            const data = await res.json();
            providerSelect.value = data.provider_type;
            ollamaHostInput.value = data.ollama_host;
            ollamaModelInput.value = data.default_model;
            
            // Trigger select event to show/hide fields
            providerSelect.dispatchEvent(new Event("change"));
            updateProviderBadge(data.provider_type, data.default_model);
        } catch (e) {
            console.error("Failed to load initial config", e);
        }
    }

    // Load static memory content
    async function fetchMemoryData() {
        try {
            const res = await fetch("/api/memory");
            memoryData = await res.json();
            renderTabContent();
        } catch (e) {
            console.error("Failed to fetch memory data", e);
        }
    }

    function renderTabContent() {
        if (!memoryData || !memoryData[activeTab]) {
            memoryEditor.value = "";
            return;
        }

        const content = memoryData[activeTab];
        
        // If content is JSON (object), stringify it
        if (typeof content === "object") {
            memoryEditor.value = JSON.stringify(content, null, 2);
            memoryEditor.readOnly = true;
            memoryEditor.classList.remove("editable");
            saveMemoryBtn.style.display = "none";
            editorStatusText.textContent = "Read-only JSON Data";
        } else {
            memoryEditor.value = content;
            memoryEditor.readOnly = false;
            memoryEditor.classList.add("editable");
            saveMemoryBtn.style.display = "block";
            editorStatusText.textContent = "Editable Markdown File";
        }
    }

    // Dynamic UI agent nodes rendering
    function updateAgentVisuals(logs) {
        // Reset all active classes
        nodeManager.classList.remove("active");
        nodePlanner.classList.remove("active");
        nodeWorker.classList.remove("active");
        nodeReviewer.classList.remove("active");
        
        linkMtoP.classList.remove("active");
        linkPtoW.classList.remove("active");
        linkWtoR.classList.remove("active");
        
        if (!isRunning) {
            nodeManager.querySelector(".node-status").textContent = "Idle";
            nodePlanner.querySelector(".node-status").textContent = "Idle";
            nodeWorker.querySelector(".node-status").textContent = "Idle";
            nodeReviewer.querySelector(".node-status").textContent = "Idle";
            return;
        }

        // Analyze last logs to find which agent is active
        let lastLines = logs.slice(-5).join("\n");
        
        if (lastLines.includes("Planning Phase") || lastLines.includes("Planner Agent")) {
            nodePlanner.classList.add("active");
            nodePlanner.querySelector(".node-status").textContent = "Planning...";
            linkMtoP.classList.add("active");
            linkMtoP.style.setProperty("--link-start", "var(--color-indigo)");
            linkMtoP.style.setProperty("--link-end", "var(--color-cyan)");
        } else if (lastLines.includes("Worker Agent")) {
            nodeWorker.classList.add("active");
            nodeWorker.querySelector(".node-status").textContent = "Coding...";
            linkPtoW.classList.add("active");
            linkPtoW.style.setProperty("--link-start", "var(--color-cyan)");
            linkPtoW.style.setProperty("--link-end", "var(--color-violet)");
        } else if (lastLines.includes("Reviewer Agent")) {
            nodeReviewer.classList.add("active");
            nodeReviewer.querySelector(".node-status").textContent = "Critiquing...";
            linkWtoR.classList.add("active");
            linkWtoR.style.setProperty("--link-start", "var(--color-violet)");
            linkWtoR.style.setProperty("--link-end", "var(--color-magenta)");
        } else {
            nodeManager.classList.add("active");
            nodeManager.querySelector(".node-status").textContent = "Coordinating...";
        }
    }

    // Render task entries
    function renderTasks(tasks) {
        if (!tasks || tasks.length === 0) {
            tasksListContainer.innerHTML = '<div class="no-tasks">No active tasks. Submit a goal to see execution steps.</div>';
            return;
        }

        tasksListContainer.innerHTML = "";
        tasks.forEach(task => {
            const card = document.createElement("div");
            card.className = "task-card";
            
            const info = document.createElement("div");
            info.className = "task-info";
            
            const desc = document.createElement("div");
            desc.className = "task-desc";
            desc.textContent = task.description;
            
            const meta = document.createElement("div");
            meta.className = "task-meta";
            meta.textContent = `ID: ${task.id} | Assignee: ${task.assignee || 'Worker'}`;
            if (task.attempts > 0) {
                meta.textContent += ` | Attempts: ${task.attempts}`;
            }
            
            info.appendChild(desc);
            info.appendChild(meta);
            
            const status = document.createElement("div");
            status.className = `task-status-pill ${task.status}`;
            status.textContent = task.status.replace("_", " ");
            
            card.appendChild(info);
            card.appendChild(status);
            tasksListContainer.appendChild(card);
        });
    }

    // Polling function
    async function pollStatus() {
        try {
            const res = await fetch("/api/status");
            const data = await res.json();
            
            isRunning = data.is_running;
            updateUIRunningState(isRunning);
            
            // Append new log lines
            if (data.logs && data.logs.length > logLineCount) {
                for (let i = logLineCount; i < data.logs.length; i++) {
                    const lineText = data.logs[i];
                    let lineClass = "";
                    if (lineText.includes("[ERROR]")) lineClass = "error-line";
                    else if (lineText.includes("APPROVED") || lineText.includes("successfully")) lineClass = "success-line";
                    appendLog(lineText, lineClass);
                }
                logLineCount = data.logs.length;
            }
            
            updateAgentVisuals(data.logs || []);
            renderTasks(data.tasks);
            
            // If execution finished, trigger memory refresh
            if (!isRunning && logLineCount > 0) {
                fetchMemoryData();
            }
        } catch (e) {
            console.error("Polling status error", e);
        }
    }

    // Initialization
    fetchInitialConfig();
    fetchMemoryData();
    
    // Start polling every 1 second
    pollInterval = setInterval(pollStatus, 1000);
});
