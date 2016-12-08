<?
	$dislike = [];
	$like = [];
	$superlike = [];
	foreach ($_POST as $id => $value) {
		if ($value == "PASS") {}
		elseif ($value == "DISLIKE") $dislike[] = $id;
		elseif ($value == "LIKE") $like[] = $id;
		elseif ($value == "SUPERLIKE") $superlike[] = $id;
	}
	
	echo "python $_POST[parent_folder]/TndrAssistant.py -dl";
	foreach ($dislike as $id) {
		echo " ".$id;
	}
	
	echo "<p>python $_POST[parent_folder]/TndrAssistant.py -L";
	foreach ($like as $id) {
		echo " ".$id;
	}
	
	echo "<p>python $_POST[parent_folder]/TndrAssistant.py -SL";
	foreach ($superlike as $id) {
		echo " ".$id;
	}
	
	echo "<p>";
?>