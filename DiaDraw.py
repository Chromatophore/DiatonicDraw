import sys
import itertools
#print "This is the name of the script: ", sys.argv[0]
#print "Number of arguments: ", len(sys.argv)
#print "The arguments are: " , str(sys.argv)

use_circle_of_fifths = True
includeArpeggios = True

colours = ("-fill \"rgb(255,155,200)\"",
		   "-fill \"rgb(255,200,155)\"",
		   "-fill \"rgb(200,255,200)\"",
		   "-fill \"rgb(200,200,255)\"",
		   "-fill \"rgb(155,200,255)\"",
		   "-fill \"rgb(200,155,255)\"",
		   "-fill \"rgb(155,255,200)\"")

##### Semitone Math:
semitones = [
"A",
"A#",
"B",
"C",
"C#",
"D",
"D#",
"E",
"F",
"F#",
"G",
"G#"
]

# Notes that are the same as one another:
equivilents = {
'F#': 'Gb',
'Gb': 'F#',
'G#': 'Ab',
'Ab': 'G#',
'A#': 'Bb',
'Bb': 'A#',
'C#': 'Db',
'Db': 'C#',
'D#': 'Eb',
'Eb': 'D#'
}

semitone_lookup = {}
i = 0
for tone in semitones:
	semitone_lookup[tone] = i
	if tone in equivilents:
		semitone_lookup[equivilents[tone]] = i
	i += 1

def create_circle_of_fifths(start_point):
	o = []
	end = start_point
	first = 1
	while (end != start_point or first):
		first = 0
		low = len(o) < 6
		add_note = semitones[start_point]
		if low and add_note in equivilents:
			add_note = equivilents[add_note]
		o.append(add_note)
		start_point = (start_point + 7) % 12
	return o

class Layout:
	def __init__(self):
		self.rows = []
		self.raw_rows = []
		self.notes = []
		self.chords = []
		self.row_count = 0

	def __str__(self):
		return str("Diatonic layout with %d rows and %d buttons" % (len(self.raw_rows), len(self.notes) / 2) )
	def __repr__(self):
		return str(self.notes)

	def AddRow(self, r):
		# Row list is expected to be a stream of PUSH PULL notes from low to high

		self.raw_rows.append(r)
		

		# Generate a list of notes.
		# This is a list of tuples in the format (N#, N, #, isPush)
		# Start on a push:
		push = True
		for n in range(len(r)):
			t = self.NoteSplit(r[n])

			semitone_score = semitone_lookup[t[0]]
			if semitone_score < semitone_lookup["C"]:
				semitone_score += 12
			semitone_score += int(t[1]) * 12

			self.notes.append( (r[n], t[0], int(t[1]), semitone_score, push, (self.row_count, n) ) ) 
			push = not push

		self.row_count += 1

		# Note sorting 
		def note_sort(t):
			# note sorting is a big pain
			# a and b come before c
			r = t[1]
			n = int(t[2])

			if r == "A" or r == "A#" or r == "Bb" or r == "B":
				n = n + 1
			return str(n) + r

		#self.notes = sorted(self.notes, key=note_sort)
		self.notes = sorted(self.notes, key=lambda x: x[3])

	def NoteSplit(self, note):
		# This splits A5 into (A, 5)
		note_name = note.rstrip("0123456789")
		octave = note[len(note_name):]
		return (note_name, octave)

	def BuildChords(self, chord_list):
		#print chord_list

		dddebug = False

		for name, makeup in chord_list:
			l = makeup.split(",")
			notes_in_chord = {}
			loose_notes = []
			for n in self.notes:
				basic = n[1]
				if basic in l:
					# if the basic note is in the chord
					# Add this note to the list of this note:
					if basic in notes_in_chord:
						notes_in_chord[basic].append(n)
					else:
						o = []
						o.append(n)
						notes_in_chord[basic] = o

					loose_notes.append(n)

			# notes_in_chord now contains all notes that we have, push or pull, that are in this chord
			# Let's built every single combination of this chord and score them:
			#print notes_in_chord

			fixed_structure = []
			for a in l:
				fixed_structure.append(notes_in_chord[a])

			all_permutes = list(itertools.product(*fixed_structure))

			scored_permutes = []
			for perm in all_permutes:
				scored_permutes.append( [0, perm] )

			# All permutes now contains every permutation of the chord. Now, let's score all of these results and pick the best one
			# After that we shall remove these notes as options, and then find the next best chord

			def score_chords(chords):
				for schord in chords:
					score = 0
					chord = schord[1]
					root_note = chord[0]

					# Step one: the lower the root note, the higher the score:
					base = root_note[3]
					score += 100 - base
					for n in chord:
						nsc = n[3]
						if nsc < base:
							score -= 50

						dist = abs(base - nsc)
						# the closer the note is to the root note, the better:
						score -= dist

						# if the direction is mixed, remove a lot of points
						if n[4] != root_note[4]:
							score -= 1000

					schord[0] = score
					#print schord

			score_chords(scored_permutes)

			scored_permutes.sort()#(key = lambda x: x[0])

			chord_results = []

			i = 0

			while len(scored_permutes) > 0 and i < 50:
				best_chord = scored_permutes[-1]
				chord_results.append(best_chord)
				if dddebug:
					print "Best chord: " + str(best_chord)
					print "There are %d records" % (len(scored_permutes))
				next_list = []

				for note in best_chord[1]:
					if note in loose_notes:
						loose_notes.remove(note)

				for a, prev_result in scored_permutes:
					exclude = 0
					for note in prev_result:
						if note in best_chord[1]:
							exclude += 1

					if exclude == 0:
						next_list.append([0,prev_result])
				
				if dddebug:
					print "There are now %d records" % (len(next_list))
					
				score_chords(next_list)
				next_list.sort()
				scored_permutes = next_list

				i += 1


			self.chords.append( (name, chord_results, loose_notes) )

		return False

	def FindChordNotes(self, chord):

		return False

	def DrawLayout(self):

		# Calculates the height of our output:
		maxlen = 0
		for row in self.raw_rows:
			maxlen = max(maxlen, len(row) / 2)
		self.width = maxlen * (distance_x) + 2 * x_border

		# Height should be, the borders on top, the total distance betwen the top of the top row and the top of the bottom row, and then
		# a single width of a circle
		self.height = y_border * 2 + (self.row_count - 1) * distance_y + circle_size

		half_circle = circle_size * 0.5
		# The starting height will be the border plus half of a circle
		row_base_height = y_border + half_circle

		# Calculate center position for text:
		center_x = self.width / 2
		center_y = self.height / 2

		# Set up the layout drawing:
		layout_output = "convert -size %sx%s xc:transparent -fill transparent -strokewidth 2  -stroke black" % (self.width, self.height)
		text_extra = " -fill black -font Arial -stroke transparent -pointsize 36 -gravity center"
		text_small = " -pointsize 24"

		self.arc_lookup = {}

		# for each row, we will draw all the buttons and lines:
		buttons_in_row = {}

		for r in range(len(self.raw_rows)):
			row = self.raw_rows[r]
			buttons = len(row) / 2
			buttons_in_row[r] = buttons

			for j in range(buttons):

				row_height = r * distance_y + row_base_height

				circle_other = row_height - half_circle
				line_low = row_height + half_circle

				q = float(j) - float( buttons - 1) / 2
				x = self.width/2 + q * distance_x

				layout_output += " -draw \"circle %d,%d %d,%d\"" % (x ,row_height, x,circle_other)
				layout_output += " -draw \"line %d,%d %d,%d\"" % (x, circle_other, x, line_low)

		# Then draw the notes afterwards:
		for note in self.notes:
			basic = note[1]
			octave = note[2]
			push = note[4]
			location = note[5]

			row_height = location[0] * distance_y + row_base_height			
			q = float(location[1] / 2) - float( buttons_in_row[location[0]] - 1) / 2
			x = self.width/2 + q * distance_x

			text_x = x - center_x

			if push:
				basic_text_x = text_x - circle_size/4 + font_shift
				octave_text_x = text_x + octave_x + font_shift
			else:
				basic_text_x = text_x + circle_size/4 + font_shift
				octave_text_x = text_x - octave_x + font_shift

			text_extra += " -draw \"text %d,%d '%s'\"" % (basic_text_x,row_height - center_y, basic)
			text_small += " -draw \"text %d,%d '%s'\"" % (octave_text_x,row_height - center_y+octave_shift,octave)

			tup = (x - half_circle + font_label_width,row_height - half_circle, x + half_circle + font_label_width, row_height + half_circle, 90, 270)

			self.arc_lookup[note] = tup

		layout_output += text_extra
		layout_output += text_small

		layout_output += " layout.png"

		return [self.width, self.height, layout_output]

	def DrawChords(self):

		if not self.chords:
			return

		output_base = "convert -size %dx%d xc:transparent " % (self.width + font_label_width,self.height)
		output_base += " -stroke black -strokewidth 3 -draw \"line %d,%d %d,%d\" -draw \"line %d,%d %d,%d\" -draw \"line %d,%d %d,%d\"" % ( font_label_width, 0, font_label_width, height, 0, height, font_label_width + width, height, 0, 0, font_label_width + width, 0)

		chord_draw = []

		for chord in self.chords:
			name = chord[0]

			# We may need to create up to 3 files depending on how we want this information to be displayed
			# We have Push, Pull and Arpeggio
			drawings = ["", "", ""]
			colour_indexes = [0,0,0]

			solutions = chord[1]
			for solution in solutions:
				if solution[0] > -1000 or includeArpeggios:
					if solution[0] <= -1000:
						use_index = 2
					elif push:
						use_index = 0
					else:
						use_index = 1

					c_index = colour_indexes[use_index]
					snew = " %s" % colours[c_index]
					colour_indexes[use_index] = colour_indexes[use_index] + 1
					push = False
					for note in solution[1]:
						arc = self.arc_lookup[note]
						push = note[4]
						snew += " -draw \"arc %d,%d %d,%d %d,%d\"" % arc

					drawings[use_index] += snew

			name_modify = [" PUSH", " PULL", " ARP"]

			for drawing in range(len(drawings)):
				if drawings[drawing]:
					chord_output = output_base
					# Write down what chord this is
					chord_output += " -stroke transparent -fill black -font Arial -pointsize 48 -gravity center -draw \"text %d,%d '%s'\"" % ( - self.width / 2, 0, name + name_modify[drawing])
					chord_output += " -gravity NorthWest"
					chord_output += drawings[drawing]
					chord_output += " layout.png -geometry +%d+0 -composite -flatten \"%s.png\"" % (font_label_width, name + name_modify[drawing])

					drawings[drawing] = (chord_output)

			for file in drawings:
				print file
			exit()




# Define the layout: We should be able to take this as a command line maybe?
row1 = ["F5","Eb5","D4","F#4","G4","A4","B4","C5","D5","E5",
		"G5","F#5","B5","A5","D6","C6","G6","E6","B6","F#6"]

row2 = ["G#4","Bb4","A3","C#4","D4","E4","F#4","G4","A4","B4",
		"D5","C#5","F#5","E5","A5","G5","D6","B5","F#6","C#6","A6","E6"]

row3 = []


### BC layout:

row1 = ["E3","A3", "G3","B3", "C4","D4", "E4","F4", "G4","A4",
	    "C5","B4", "E5","D5", "G5","F5", "C6","A5", "E6","B5"]
row2 = ["D#3","G#3", "F#3","A#3", "B3","C#4", "D#4","E4", "F#4","G#4", "B4","A#4",
        "D#5","C#5", "F#5","E5", "B5","G#5", "D#6","A#5", "F#6", "C#6"]



lay = Layout()
lay.AddRow(row1)
lay.AddRow(row2)


anchor_note = "G#"
circle_start_point = (semitones.index(anchor_note.upper())) % 12

output_order = (create_circle_of_fifths(circle_start_point))

chords = []
def create_chords(root_notes, chord_patterns):
	o = []
	for root_note in root_notes:
		for pattern in chord_patterns:
			name = pattern[0]
			offsets = pattern[1].split(",")
			chord = []
			semitone_number = semitone_lookup[root_note]
			for offset in offsets:
				chord.append(semitones[(semitone_number + int(offset)) % 12])

			root_name = root_note;
			if root_note in equivilents:
				root_name += "~" + equivilents[root_name]

			o.append(( "%s %s" % (root_name, name) , ','.join(chord) ) )

	return o

all_chords = create_chords(output_order,(
	("Major", "0,4,7"),
	("+7", "0,4,7,10"),
#	("+Maj7", "0,4,7,11"),
	("Minor", "0,3,7"),
	("-7", "0,3,7,10"),
#	("-Maj7", "0,3,7,11"),
	("I V", "0,7"),
#	("I +III", "0,4"),
#	("I -III", "0,3"),
#	("-III V", "4,7"),
#	("+III V", "3,7"),
	 ))

push_notes = []
pull_notes = []
all_notes = []

# Now let's generate information for the layout

lay.BuildChords(all_chords)


#convert -size 100x100 xc:skyblue -fill transparent -stroke black -draw "circle 50,30 50,10" -draw "line 50,10 50,50" -fill black -font Arial -draw "text 10,10 'Anthony'" circle.png
#convert -size 300x300 xc:skyblue -fill transparent -strokewidth 2 -stroke black -draw "circle 150,90 150,30" -draw "line 150,30 150,150" -fill black -font Arial -stroke transparent -pointsize 36 -gravity center -draw "text -27,-60 'A'" -draw "text 33,-60 'F#'" circle.png
#convert -size 300x300 xc:skyblue -fill transparent -strokewidth 2 -stroke black -draw "circle 150,90 150,30" -draw "line 150,30 150,150" -fill black -font Arial -stroke transparent -pointsize 36 -gravity center -draw "text -27,-60 'IIIIII'" -draw "text 32,-60 'IIIIII'" circle.png

circle_size = 120
distance_x = 150
distance_y = 120
x_border = 50
y_border = 50
font_shift = 2
octave_shift = 40
octave_x = 15
font_label_width = 500

chords_per_page = 9

layout_result = lay.DrawLayout()

width = layout_result[0]
height = layout_result[1]
layout_output = layout_result[2]

lay.DrawChords()

exit()

partial_high = 1
chord_files = []

def generate_output(valid_chords, matching_notes, arc_lookup, output_files):
	for chord_set in valid_chords:
		# For all the notes in the valid chord:
		colour_index = 0
		notes = chord_set[1].split(',')

		chord_output = "convert -size %dx%d xc:transparent " % (width + font_label_width,height)

		notes_copy = list(notes)
		solution = []
		exclude = []

		chord_output += " -stroke black -strokewidth 3 -draw \"line %d,%d %d,%d\" -draw \"line %d,%d %d,%d\" -draw \"line %d,%d %d,%d\"" % ( font_label_width, 0, font_label_width, height, 0, height, font_label_width + width, height, 0, 0, font_label_width + width, 0)
		chord_output += " -stroke transparent -fill black -font Arial -pointsize 48 -gravity center -draw \"text %d,%d '%s'\"" % ( - width / 2, 0, chord_set[0])

		chord_output += " -gravity NorthWest"

		# We iterate over every note in the layout because we may have multiple solutions
		for note_pair in matching_notes:
			note = note_pair[0]
			equiv_note = ""
			try:
				equiv_note = equivilents[note]
			except KeyError:
				equiv_note = ""

			#if not notes in notes_copy and equiv_note in notes_copy:
				#note = equiv_note

			fullnote = note + note_pair[1]
			if (note in notes_copy or equiv_note in notes_copy) and not (fullnote in exclude):
				exclude.append(fullnote)
#				if not note in notes_copy:
#					note = equiv_note
#					fullnote = note + note_pair[1]
#					exclude.append(fullnote)

				solution.append(fullnote)

				try:
					notes_copy.remove(note)
				except:
					notes_copy.remove(equiv_note)


				# if the list is finally empty:
				if not notes_copy:
					#print chord_set[0] + ": " + str(solution)

					chord_output += " %s" % colours[colour_index]
					
					for result in solution:
						for arc in arc_lookup[result]:
							chord_output += " -draw \"arc %d,%d %d,%d %d,%d\"" % arc

					colour_index += 1
					solution = []
					notes_copy = list(notes)

		if colour_index > 0 and partial_high and solution:
			chord_output += " %s" % "-fill \"rgb(200,200,200)\""
			for result in solution:
				for arc in arc_lookup[result]:
					chord_output += " -draw \"arc %d,%d %d,%d %d,%d\"" % arc

		filename = "%s" % chord_set[0]
		chord_output += " layout.png -geometry +%d+0 -composite -flatten \"%s.png\"" % (font_label_width, filename)

		output_files.append(filename)
		print chord_output

print layout_output
generate_output(valid_push_chords, push_notes, push_arc_lookup, chord_files)
generate_output(valid_pull_chords, pull_notes, pull_arc_lookup, chord_files)

# Generate pages:
succeeded = 0
remaining = chords_per_page
page_number = 1
page = ""
while succeeded == 0:

	remaining -= 1

	if chord_files:
		extra = chord_files[0]
		del chord_files[0]

		if remaining == chords_per_page - 1 and extra: 
			page = "convert \"%s.png\"" % (extra)
		else:
			page += " \"%s.png\" -append" % (extra)

	else:
		extra = "";

	if remaining == 0:
		if chord_files:
			page += " page%d.png" % (page_number)
			page_number += 1
			print page
			page = ""
			remaining = chords_per_page
		else:
			succeeded = 1

if page:
	page += " page%d.png" % (page_number)
	print page

#print layout_output
#print push_arc_lookup