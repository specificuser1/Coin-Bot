<?php
session_start();

define('BOT_API_URL', getenv('BOT_API_URL') ?: 'http://localhost:5000');
define('ADMIN_USERNAME', getenv('ADMIN_USERNAME') ?: 'admin');
define('ADMIN_PASSWORD', getenv('ADMIN_PASSWORD') ?: 'admin123');
define('DATA_DIR', __DIR__ . '/../bot/data/');
define('KEYS_DIR', __DIR__ . '/../bot/keys/');

// API Functions
function callBotAPI($endpoint, $method = 'GET', $data = null) {
    $ch = curl_init(BOT_API_URL . $endpoint);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
    
    if ($data) {
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    }
    
    $response = curl_exec($ch);
    curl_close($ch);
    
    return json_decode($response, true);
}

function getBotStatus() {
    return callBotAPI('/status');
}

function restartBot() {
    return callBotAPI('/restart', 'POST');
}

function stopBot() {
    return callBotAPI('/stop', 'POST');
}

function startBot() {
    return callBotAPI('/start', 'POST');
}

function getCoinsData() {
    $file = DATA_DIR . 'coins.json';
    if (file_exists($file)) {
        return json_decode(file_get_contents($file), true);
    }
    return [];
}

function getUnusedKeys() {
    $file = KEYS_DIR . 'unused_keys.txt';
    if (file_exists($file)) {
        return array_filter(explode("\n", file_get_contents($file)));
    }
    return [];
}

function getRedeemedKeys() {
    $file = KEYS_DIR . 'redeemed_keys.txt';
    if (file_exists($file)) {
        $keys = [];
        $lines = array_filter(explode("\n", file_get_contents($file)));
        foreach ($lines as $line) {
            $parts = explode('|', $line);
            $keys[] = [
                'key' => $parts[0],
                'redeemed_at' => $parts[1] ?? 'Unknown',
                'user' => $parts[2] ?? 'Unknown'
            ];
        }
        return $keys;
    }
    return [];
}

function addKeys($keys) {
    $file = KEYS_DIR . 'unused_keys.txt';
    $current = file_get_contents($file);
    file_put_contents($file, $current . "\n" . implode("\n", $keys));
    return count($keys);
}

function getBlacklistedUsers() {
    $data = getCoinsData();
    $blacklisted = [];
    foreach ($data as $user_id => $user_data) {
        if (isset($user_data['blacklisted']) && $user_data['blacklisted']) {
            $blacklisted[$user_id] = $user_data;
        }
    }
    return $blacklisted;
}

function blacklistUser($user_id) {
    $data = getCoinsData();
    if (isset($data[$user_id])) {
        $data[$user_id]['blacklisted'] = true;
        file_put_contents(DATA_DIR . 'coins.json', json_encode($data, JSON_PRETTY_PRINT));
        return true;
    }
    return false;
}

function unblacklistUser($user_id) {
    $data = getCoinsData();
    if (isset($data[$user_id])) {
        unset($data[$user_id]['blacklisted']);
        file_put_contents(DATA_DIR . 'coins.json', json_encode($data, JSON_PRETTY_PRINT));
        return true;
    }
    return false;
}

function saveEmbedSettings($settings) {
    $file = DATA_DIR . 'embed_settings.json';
    file_put_contents($file, json_encode($settings, JSON_PRETTY_PRINT));
}

function getEmbedSettings() {
    $file = DATA_DIR . 'embed_settings.json';
    if (file_exists($file)) {
        return json_decode(file_get_contents($file), true);
    }
    return [
        'title' => 'Coin System',
        'description' => 'Server Rules and Key System',
        'color' => '#00FF00',
        'image' => '',
        'thumbnail' => '',
        'footer' => 'Programmed by SUBHAN'
    ];
}
?>
