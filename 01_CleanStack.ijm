// ================== Function definition ==================
function makeMontage(dir, pure_filename){
	//Montage for checking quality of masking
	run("Z Project...", "projection=[Max Intensity]");
	rename("MASKED_MAX");
	selectImage("MAX");
	run("RGB Color");
	selectImage("MAX_BLUR");
	run("RGB Color");
	selectImage("MASK");
	run("RGB Color");
	selectImage("MASKED_MAX");
	run("RGB Color");
	run("Images to Stack", "use");
	run("Make Montage...", "columns=4 rows=1 scale=1.00 font=24 label");
	saveAs("Png", dir + "/02_cleaned/montage/" + pure_filename + "_montage.tif");
}

function Clean(dir, file) {
	// Open stack
	open(dir + "01_tif/" + file);
	
	// Obtain the filename without extension for later handling
	pure_filename = File.nameWithoutExtension;
	
	// Make mask using Z projection
	rename("RAW");
	run("Z Project...", "projection=[Max Intensity]");
	rename("MAX");
	run("Duplicate...", "duplicate");
	run("Gaussian Blur...", "sigma=5");
	rename("MAX_BLUR");
	setAutoThreshold("Default dark no-reset");
	setOption("BlackBackground", true);
	run("Convert to Mask");
	run("Fill Holes");
	run("Dilate");
	
	run("Analyze Particles...", "size=500-Infinity circularity=0.00-1.00 show=Masks display add");
	// Find the particle closest to the center
	getDimensions(width, height, channels, slices, frames);
	minDist = -1;
	closestIndex = -1;
	resultCount = getValue("results.count");
	
	for (j=0; j<resultCount; j++) {
			x = getResult("X", j);
			y = getResult("Y", j);
			dist = sqrt((x-50)*(x-50) + (y-50)*(y-50));
			if (minDist==-1 || dist<minDist) {
				minDist = dist;
				closestIndex = j;
			}
	}
	
	if (closestIndex > -1) {
		run("Multiply...", "value=0.000");
		roiManager("Select", closestIndex);
		run("Add...", "value=1");
		run("glasbey_on_dark");
		saveAs("Tiff", dir + "/02_cleaned/masks/" + pure_filename + "_mask.tif");
		rename("MASK");
	}

	// Apply mask to original stack
	imageCalculator("Multiply create stack", "RAW","MASK");
	rename("MASKED");
	
	// Make montage for checking quality of masking
	makeMontage(dir, pure_filename);

	// Save masked stack
	selectImage("MASKED");
	saveAs("Tiff", dir + "/02_cleaned/" + pure_filename + "_masked.tif");

	// Clean up any previous ROIs and results
	roiManager("Deselect");
	roiManager("Delete");
	run("Clear Results");

	// Close to free up memory
	close("*");
}

// Check if directory exists, and create one if not
function MakeDir(dir) {
	if(!File.exists(dir)){
		File.makeDirectory(dir);
		print("Directory created: " + dir);
	} else {
		print("Found: " + dir);
	}
}

// ================== Execution ==================

// Select working directory which contains the folder 'raw' with the images to be analysed
parentDir = getDirectory("Select directory");
inDir = parentDir +  "/01_tif";
outDir = parentDir +  "/02_cleaned"; 
checkDir = outDir +  "/montage";
maskDir = outDir + "/masks";

if(!File.exists(inDir)){
	print("ERROR: Required directory not found: " + inDir);
	exit();
} else {
	print("Found: " + inDir);
}

MakeDir(outDir);
MakeDir(checkDir);
MakeDir(maskDir);

// Batch mode: don't display windows during processing
setBatchMode(true);
run("Set Measurements...", "centroid redirect=None decimal=3");

// Execute function for all files in selected directory
list = getFileList(inDir);
for (i = 0; i < list.length; i++) {
	if (!endsWith(list[i], ".tif")){
		print("Skipping non-tif file: " + list[i]);
		continue;
	}
	else{
		Clean(parentDir, list[i]);
	}
}

// Notify once done
print("Finished!");

// Turn off batch mode
setBatchMode(false);
