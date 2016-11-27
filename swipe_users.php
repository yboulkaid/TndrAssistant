<?
	$dislike = [];
	$like = [];
	$superlike = [];
	foreach ($_POST as $id => $value) {
		if ($value == "NULL") {}
		elseif ($value == 0) $dislike[] = $id;
		elseif ($value == 1) $like[] = $id;
		elseif ($value == 2) $superlike[] = $id;
	}
	
	echo "python TndrAssistant.py -dl";
	foreach ($dislike as $id) {
		echo " ".$id;
	}
	
	echo "<p>python TndrAssistant.py -L";
	foreach ($like as $id) {
		echo " ".$id;
	}
	
	echo "<p>python TndrAssistant.py -SL";
	foreach ($superlike as $id) {
		echo " ".$id;
	}
	
	echo "<p>";
?>