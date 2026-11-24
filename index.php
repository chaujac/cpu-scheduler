<?php /* index.php - main UI shell; all behaviour lives in js/app.js */ ?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CPU Scheduler - CS 3104N Group 9</title>
  <link rel="stylesheet" href="css/style.css?v=<?= filemtime(__DIR__ . '/css/style.css') ?>">
</head>
<body>
<aside class="sidebar">
  <div class="brand"><h1>CPU Scheduler</h1><p>CS 3104N &bull; Group 9</p></div>
  <nav><a class="tab active" href="#">Simulator</a></nav>
  <button id="presetBtn" class="btn ghost" type="button">Load edge-case preset</button>
</aside>

<main class="content">
  <div id="error" class="banner" role="alert" hidden></div>

  <section class="card">
    <h2>Processes</h2>
    <table class="input-table">
      <thead><tr><th>PID</th><th>Arrival time</th><th>Burst time</th><th></th></tr></thead>
      <tbody id="rows"></tbody>
    </table>
    <button id="addBtn" class="btn ghost" type="button">+ Add Process</button>
  </section>

  <section class="card">
    <h2>Algorithm</h2>
    <div class="algos">
      <label><input type="radio" name="algo" value="FCFS" checked> First-Come, First-Served</label>
      <label><input type="radio" name="algo" value="SJF"> Shortest-Job-First</label>
      <label><input type="radio" name="algo" value="RR"> Round Robin</label>
    </div>
    <div id="tqBox" class="tq" hidden>
      <label for="tq">Time quantum</label>
      <input id="tq" type="number" min="1" step="1" value="2">
    </div>
    <button id="runBtn" class="btn primary" type="button">Run Simulation</button>
  </section>

  <section class="card" id="ganttCard" hidden>
    <h2>Gantt chart</h2>
    <div id="gantt" class="track"></div>
  </section>

  <section class="card" id="resultCard" hidden>
    <h2>Results</h2>
    <div class="pills">
      <div class="pill"><span>Average Turnaround Time</span><strong id="avgTat">0</strong></div>
      <div class="pill"><span>Average Waiting Time</span><strong id="avgWt">0</strong></div>
    </div>
    <div class="scroll">
      <table class="result-table">
        <thead><tr><th>PID</th><th>AT</th><th>BT</th><th>CT</th><th>TAT</th><th>WT</th></tr></thead>
        <tbody id="results"></tbody>
      </table>
    </div>
  </section>
</main>
<script src="js/app.js?v=<?= filemtime(__DIR__ . '/js/app.js') ?>"></script>
</body>
</html>
