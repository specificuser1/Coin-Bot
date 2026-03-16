<?php
header('Content-Type: application/json');
require_once 'config.php';

if (!isset($_SESSION['admin_logged_in']) || $_SESSION['admin_logged_in'] !== true) {
    http_response_code(401);
    echo json_encode(['error' => 'Unauthorized']);
    exit;
}

$endpoint = $_GET['endpoint'] ?? '';

switch ($endpoint) {
    case 'status':
        echo json_encode(getBotStatus());
        break;
        
    case 'logs':
        header('Content-Type: text/plain');
        $log_file = __DIR__ . '/../bot/logs/bot.log';
        if (file_exists($log_file)) {
            echo file_get_contents($log_file);
        } else {
            echo 'No logs available';
        }
        break;
        
    case 'vc_stats':
        $stats = [
            'total_users' => 0,
            'members' => []
        ];
        // This would be populated from bot API
        echo json_encode($stats);
        break;
        
    case 'vc_settings':
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            $data = json_decode(file_get_contents('php://input'), true);
            file_put_contents(DATA_DIR . 'vc_settings.json', json_encode($data));
            echo json_encode(['success' => true]);
        }
        break;
        
    default:
        http_response_code(404);
        echo json_encode(['error' => 'Endpoint not found']);
}
?>
