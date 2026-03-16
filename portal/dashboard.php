<?php
require_once 'config.php';

if (!isset($_SESSION['admin_logged_in']) || $_SESSION['admin_logged_in'] !== true) {
    header('Location: login.php');
    exit;
}

// Handle actions
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    if (isset($_POST['action'])) {
        switch ($_POST['action']) {
            case 'restart_bot':
                restartBot();
                $message = 'Bot restart initiated';
                break;
            case 'stop_bot':
                stopBot();
                $message = 'Bot stopped';
                break;
            case 'start_bot':
                startBot();
                $message = 'Bot started';
                break;
            case 'add_keys':
                if (isset($_POST['keys'])) {
                    $keys = array_filter(explode("\n", $_POST['keys']));
                    $count = addKeys($keys);
                    $message = "Added $count keys";
                }
                break;
            case 'blacklist':
                if (isset($_POST['user_id'])) {
                    blacklistUser($_POST['user_id']);
                    $message = "User blacklisted";
                }
                break;
            case 'unblacklist':
                if (isset($_POST['user_id'])) {
                    unblacklistUser($_POST['user_id']);
                    $message = "User unblacklisted";
                }
                break;
            case 'save_embed':
                saveEmbedSettings([
                    'title' => $_POST['title'],
                    'description' => $_POST['description'],
                    'color' => $_POST['color'],
                    'image' => $_POST['image'],
                    'thumbnail' => $_POST['thumbnail'],
                    'footer' => $_POST['footer']
                ]);
                $message = "Embed settings saved";
                break;
        }
    }
}

$bot_status = getBotStatus();
$coins_data = getCoinsData();
$unused_keys = getUnusedKeys();
$redeemed_keys = getRedeemedKeys();
$blacklisted = getBlacklistedUsers();
$embed_settings = getEmbedSettings();

// Get VC stats
$vc_stats = callBotAPI('/vc_stats');
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot System Portal - Dashboard</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="dashboard">
        <div class="sidebar">
            <div class="sidebar-header">
                <h2>🤖 Bot Portal</h2>
            </div>
            <ul class="nav">
                <li><a href="#overview" class="active">Overview</a></li>
                <li><a href="#keys">Key Management</a></li>
                <li><a href="#users">Users</a></li>
                <li><a href="#blacklist">Blacklist</a></li>
                <li><a href="#vc">VC Settings</a></li>
                <li><a href="#embed">Embed Editor</a></li>
                <li><a href="#logs">Logs</a></li>
                <li><a href="logout.php">Logout</a></li>
            </ul>
        </div>
        
        <div class="main-content">
            <?php if (isset($message)): ?>
                <div class="alert alert-success"><?php echo $message; ?></div>
            <?php endif; ?>
            
            <!-- Overview Section -->
            <section id="overview" class="section active">
                <h2>System Overview</h2>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>Bot Status</h3>
                        <div class="stat-value <?php echo $bot_status['online'] ? 'status-online' : 'status-offline'; ?>">
                            <?php echo $bot_status['online'] ? 'Online' : 'Offline'; ?>
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <h3>Servers</h3>
                        <div class="stat-value"><?php echo $bot_status['guilds'] ?? 0; ?></div>
                    </div>
                    
                    <div class="stat-card">
                        <h3>Users in VC</h3>
                        <div class="stat-value"><?php echo $vc_stats['total_users'] ?? 0; ?></div>
                    </div>
                    
                    <div class="stat-card">
                        <h3>Latency</h3>
                        <div class="stat-value"><?php echo $bot_status['latency'] ?? '0'; ?>ms</div>
                    </div>
                </div>
                
                <div class="control-panel">
                    <h3>Bot Controls</h3>
                    <form method="POST" style="display: inline;">
                        <input type="hidden" name="action" value="restart_bot">
                        <button type="submit" class="btn btn-warning">Restart Bot</button>
                    </form>
                    
                    <form method="POST" style="display: inline;">
                        <input type="hidden" name="action" value="stop_bot">
                        <button type="submit" class="btn btn-danger">Stop Bot</button>
                    </form>
                    
                    <form method="POST" style="display: inline;">
                        <input type="hidden" name="action" value="start_bot">
                        <button type="submit" class="btn btn-success">Start Bot</button>
                    </form>
                </div>
                
                <div class="live-stats">
                    <h3>Live VC Members</h3>
                    <div class="stats-table">
                        <table>
                            <thead>
                                <tr>
                                    <th>Server</th>
                                    <th>Channel</th>
                                    <th>User</th>
                                    <th>Screen Share</th>
                                    <th>Earning</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php foreach (($vc_stats['members'] ?? []) as $member): ?>
                                <tr>
                                    <td><?php echo $member['guild']; ?></td>
                                    <td><?php echo $member['channel']; ?></td>
                                    <td><?php echo $member['name']; ?></td>
                                    <td><?php echo $member['screenshare'] ? '✅' : '❌'; ?></td>
                                    <td><?php echo $member['earning'] ? '✅' : '❌'; ?></td>
                                </tr>
                                <?php endforeach; ?>
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>
            
            <!-- Key Management Section -->
            <section id="keys" class="section">
                <h2>Key Management</h2>
                
                <div class="key-stats">
                    <div class="stat-card">
                        <h3>Available Keys</h3>
                        <div class="stat-value"><?php echo count($unused_keys); ?></div>
                    </div>
                    
                    <div class="stat-card">
                        <h3>Redeemed Keys</h3>
                        <div class="stat-value"><?php echo count($redeemed_keys); ?></div>
                    </div>
                </div>
                
                <div class="add-keys">
                    <h3>Add New Keys</h3>
                    <form method="POST">
                        <input type="hidden" name="action" value="add_keys">
                        <div class="form-group">
                            <label for="keys">Keys (one per line)</label>
                            <textarea id="keys" name="keys" rows="10" placeholder="KEY1&#10;KEY2&#10;KEY3"></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary">Add Keys</button>
                    </form>
                </div>
                
                <div class="redeemed-history">
                    <h3>Redeemed Keys History</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Key</th>
                                <th>Redeemed At</th>
                                <th>User</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($redeemed_keys as $key): ?>
                            <tr>
                                <td><?php echo $key['key']; ?></td>
                                <td><?php echo $key['redeemed_at']; ?></td>
                                <td><?php echo $key['user']; ?></td>
                            </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                </div>
            </section>
            
            <!-- Blacklist Section -->
            <section id="blacklist" class="section">
                <h2>Blacklist Management</h2>
                
                <div class="add-blacklist">
                    <h3>Blacklist User</h3>
                    <form method="POST">
                        <input type="hidden" name="action" value="blacklist">
                        <div class="form-group">
                            <label for="user_id">User ID</label>
                            <input type="text" id="user_id" name="user_id" required>
                        </div>
                        <button type="submit" class="btn btn-danger">Blacklist User</button>
                    </form>
                </div>
                
                <div class="blacklist-list">
                    <h3>Blacklisted Users</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>User ID</th>
                                <th>Coins</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($blacklisted as $user_id => $user): ?>
                            <tr>
                                <td><?php echo $user_id; ?></td>
                                <td><?php echo $user['coins']; ?></td>
                                <td>
                                    <form method="POST" style="display: inline;">
                                        <input type="hidden" name="action" value="unblacklist">
                                        <input type="hidden" name="user_id" value="<?php echo $user_id; ?>">
                                        <button type="submit" class="btn btn-small btn-success">Unblacklist</button>
                                    </form>
                                </td>
                            </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                </div>
            </section>
            
            <!-- VC Settings Section -->
            <section id="vc" class="section">
                <h2>Voice Channel Settings</h2>
                
                <div class="vc-settings">
                    <h3>Coin Earnings Configuration</h3>
                    <form id="vcForm">
                        <div class="form-group">
                            <label>Coin per minute (base)</label>
                            <input type="number" id="coin_per_minute" value="1.0" step="0.1">
                        </div>
                        
                        <div class="form-group">
                            <label>Screen share bonus</label>
                            <input type="number" id="screen_bonus" value="0.5" step="0.1">
                        </div>
                        
                        <div class="form-group">
                            <label>Min account age (days)</label>
                            <input type="number" id="min_age" value="28">
                        </div>
                        
                        <div class="form-group">
                            <label>Earning VC IDs (comma separated)</label>
                            <input type="text" id="vc_ids" placeholder="123456789,987654321">
                            <small>Leave empty for all VCs</small>
                        </div>
                        
                        <button type="button" class="btn btn-primary" onclick="saveVCSettings()">Save Settings</button>
                    </form>
                </div>
            </section>
            
            <!-- Embed Editor Section -->
            <section id="embed" class="section">
                <h2>Embed Editor</h2>
                
                <form method="POST">
                    <input type="hidden" name="action" value="save_embed">
                    
                    <div class="form-group">
                        <label for="title">Title</label>
                        <input type="text" id="title" name="title" value="<?php echo $embed_settings['title']; ?>" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="description">Description</label>
                        <textarea id="description" name="description" rows="5" required><?php echo $embed_settings['description']; ?></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="color">Color (Hex)</label>
                        <input type="color" id="color" name="color" value="<?php echo $embed_settings['color']; ?>">
                    </div>
                    
                    <div class="form-group">
                        <label for="image">Image URL</label>
                        <input type="url" id="image" name="image" value="<?php echo $embed_settings['image']; ?>">
                    </div>
                    
                    <div class="form-group">
                        <label for="thumbnail">Thumbnail URL</label>
                        <input type="url" id="thumbnail" name="thumbnail" value="<?php echo $embed_settings['thumbnail']; ?>">
                    </div>
                    
                    <div class="form-group">
                        <label for="footer">Footer</label>
                        <input type="text" id="footer" name="footer" value="<?php echo $embed_settings['footer']; ?>" required>
                    </div>
                    
                    <button type="submit" class="btn btn-primary">Save Embed Settings</button>
                </form>
                
                <div class="embed-preview">
                    <h3>Preview</h3>
                    <div class="embed-box">
                        <div class="embed-title" id="preview-title"><?php echo $embed_settings['title']; ?></div>
                        <div class="embed-description" id="preview-description"><?php echo $embed_settings['description']; ?></div>
                        <div class="embed-footer" id="preview-footer"><?php echo $embed_settings['footer']; ?></div>
                    </div>
                </div>
            </section>
            
            <!-- Logs Section -->
            <section id="logs" class="section">
                <h2>Bot Console Logs</h2>
                
                <div class="log-container">
                    <pre id="log-output">Loading logs...</pre>
                </div>
                
                <button class="btn btn-primary" onclick="refreshLogs()">Refresh Logs</button>
            </section>
        </div>
    </div>
    
    <script>
        // Tab switching
        document.querySelectorAll('.nav a').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                
                document.querySelectorAll('.nav a').forEach(a => a.classList.remove('active'));
                link.classList.add('active');
                
                document.querySelectorAll('.section').forEach(section => {
                    section.classList.remove('active');
                });
                
                const target = link.getAttribute('href').substring(1);
                document.getElementById(target).classList.add('active');
            });
        });
        
        // Live log updates
        function refreshLogs() {
            fetch('api.php?endpoint=logs')
                .then(response => response.text())
                .then(data => {
                    document.getElementById('log-output').textContent = data;
                });
        }
        
        setInterval(refreshLogs, 5000);
        
        // Embed preview updates
        document.querySelectorAll('#embed input, #embed textarea').forEach(input => {
            input.addEventListener('input', () => {
                document.getElementById('preview-title').textContent = document.getElementById('title').value;
                document.getElementById('preview-description').textContent = document.getElementById('description').value;
                document.getElementById('preview-footer').textContent = document.getElementById('footer').value;
            });
        });
        
        // VC Settings
        function saveVCSettings() {
            const data = {
                coin_per_minute: document.getElementById('coin_per_minute').value,
                screen_bonus: document.getElementById('screen_bonus').value,
                min_age: document.getElementById('min_age').value,
                vc_ids: document.getElementById('vc_ids').value.split(',').map(id => id.trim())
            };
            
            fetch('api.php?endpoint=vc_settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                alert('Settings saved!');
            });
        }
    </script>
</body>
</html>
