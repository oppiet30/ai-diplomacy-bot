<?php
// Invoke webDiplomacy's actual adjudicator without starting a game or web server.
// Only the explicitly named, disposable test database on loopback is permitted.
define('IN_CODE', true);
error_reporting(E_ALL & ~E_DEPRECATED);
$root = realpath($argv[1]);
if (!$root || !is_file($root.'/gamemaster/adjudicator/diplomacy.php')) {
    throw new RuntimeException('Expected a webDiplomacy source checkout');
}
function l_r($path) { global $root; return $root.'/'.$path; }
function l_t($message) { return $message; }
require l_r('gamemaster/adjudicator/diplomacy.php');
class TestDatabase {
    public $pdo;
    function __construct() {
        $this->pdo = new PDO('mysql:host=127.0.0.1;port=3307;dbname=adjudicator_compat_test',
            'adjudicator_test', 'local-test-only', [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
        $this->pdo->exec("SET SESSION sql_mode=''");
    }
    function sql_put($query) { return $this->pdo->exec($query); }
    function sql_tabl($query) { return $this->pdo->query($query); }
    function tabl_row($statement) { return $statement->fetch(PDO::FETCH_NUM); }
    function tabl_hash($statement) { return $statement->fetch(PDO::FETCH_ASSOC); }
}
class TestVariant {
    public $mapID = 1;
    function __call($class, $args) { return new $class(...$args); }
}
$DB = new TestDatabase();
$Game = (object)['Variant' => new TestVariant()];
$GLOBALS['GAMEID'] = 1;
$input = json_decode(stream_get_contents(STDIN), true, 512, JSON_THROW_ON_ERROR);
$schema = file_get_contents(l_r('install/FullInstall/fullInstall.sql'));
$created = [];
try {
    foreach (['wD_Moves', 'wD_Borders'] as $table) {
        if (!preg_match('/CREATE TABLE `'.preg_quote($table, '/').'` \(.*?\) ENGINE=.*?;/s', $schema, $matches)) {
            throw new RuntimeException('Missing test schema: '.$table);
        }
        // No DROP or IF NOT EXISTS: refuse to overwrite a pre-existing table.
        $DB->sql_put($matches[0]);
        $created[] = $table;
    }
    $insertBorder = $DB->pdo->prepare('INSERT INTO wD_Borders (mapID,fromTerrID,toTerrID,armysPass,fleetsPass) VALUES (1,?,?,?,?)');
    foreach ($input['borders'] as $edge) { $insertBorder->execute($edge); }
    $insertMove = $DB->pdo->prepare('INSERT INTO wD_Moves (id,gameID,orderID,unitID,countryID,moveType,terrID,toTerrID,fromTerrID,viaConvoy) VALUES (?,1,?,?,?,?,?,?,?,?)');
    $output = [];
    foreach ($input['cases'] as $case) {
        $DB->sql_put('DELETE FROM wD_Moves');
        foreach ($case['orders'] as $row) {
            $insertMove->execute([$row['id'], $row['id'], $row['id'], $row['countryID'],
                $row['type'], $row['terrID'], $row['toTerrID'], $row['fromTerrID'], $row['viaConvoy']]);
        }
        (new adjudicatorDiplomacy())->adjudicate();
        $output[$case['name']] = [];
        $result = $DB->sql_tabl('SELECT id,success,dislodged FROM wD_Moves ORDER BY id');
        while ($row = $DB->tabl_hash($result)) {
            $original = $case['orders'][$row['id'] - 1];
            $output[$case['name']][strval($row['id'])] = [
                'move_success' => $original['type'] === 'Move' && $row['success'] === 'Yes',
                'dislodged' => $row['dislodged'] === 'Yes'
            ];
        }
    }
    echo json_encode($output, JSON_THROW_ON_ERROR);
} finally {
    foreach (array_reverse($created) as $table) { $DB->sql_put('DROP TABLE '.$table); }
}
