structure = [
	{
        "id" : "name",
		"type" : "text",
		"label" : "footprint name",
		"default" : "COIL_GENERATOR",
        "datatype" : "str",
		"unit" : None
	},{
        "id" : "layer_count",
		"type" : "choices_from_board",
		"label" : "layer count",
        "choices_source" : "COPPER_LAYER_COUNT",
        "default" : 1,
        "datatype" : "int",
		"unit" : "layer"
	},{
        "id" : "turns_count",
		"type" : "text",
		"label" : "turns per layer",
		"default" : 12,
        "datatype" : "int",
		"unit" : None
	},{
        "id" : "outer_diameter",
		"type" : "text",
		"label" : "outer diameter",
		"default" : 12.0,
        "datatype" : "float",
		"unit" : "mm"
	},{
        "id" : "turn_direction",
		"type" : "choices",
		"label" : "turn direction",
		"choices" : ["clockwise", "counter clockwise"],
        "choices_data" : [True, False],
		"default" : 0,
        "datatype" : "bool",
		"unit" : None
	},{
        "id" : "trace_width",
		"type" : "text",
		"label" : "trace width",
		"default" : 0.127,
        "datatype" : "float",
		"unit" : "mm"
	},{
        "id" : "trace_spacing",
		"type" : "text",
		"label" : "trace spacing",
		"default" : 0.127,
        "datatype" : "float",
		"unit" : "mm"
	},{
        "id" : "via_outer",
		"type" : "text",
		"label" : "via outer diameter",
		"default" : 0.6,
        "datatype" : "float",
		"unit" : "mm"
	},{
        "id" : "via_drill",
		"type" : "text",
		"label" : "via drill diameter",
		"default" : 0.3,
        "datatype" : "float",
		"unit" : "mm"
	}
]
