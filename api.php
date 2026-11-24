<?php
// api.php - JSON POST endpoint: validates input, runs the scheduler, returns JSON
require __DIR__ . '/backend/scheduler.php';
header('Content-Type: application/json; charset=utf-8');

// Small helper: send JSON + HTTP status code, then stop
function respond(int $code, array $body): void { http_response_code($code); echo json_encode($body); exit; }

if ($_SERVER['REQUEST_METHOD'] !== 'POST') respond(405, ['error' => 'Use POST.']);

$data = json_decode(file_get_contents('php://input'), true); // read raw JSON body
if (!is_array($data)) respond(400, ['error' => 'Invalid JSON body.']);

$errors = Scheduler::validate($data);                         // server-side validation
if ($errors) respond(400, ['error' => implode(' ', $errors), 'errors' => $errors]);

try {
    $sim = new Scheduler($data['processes']);
    respond(200, $sim->run($data['algorithm'], (int)($data['quantum'] ?? 1)));
} catch (Throwable $e) {
    respond(500, ['error' => 'Server error while simulating.']);
}
