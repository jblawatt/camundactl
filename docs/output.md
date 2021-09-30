# Output

[TOC]

## `output` Option

The `-o/--output` option defines the output format. The default ist `table`. All other options are described in the following.

## Table Output

The camunda responses are nearly all of type `application/json`. If the response is of type `array` a table will be printed. If it's an `object` a table with `key` and `value` headers are used.

**Options**

- `-o table`
- `-oH`, `--output-headers` gives the possibility to select the columns to show
- `-oCL`, `--output-cell-length` cell values of type string are limited to `40` characters.

_Example_

```bash
$ cctl get processInstances -o table -oH id,suspended
```

## JSON Output

Prints the json API response with end indent of 2.

**Options**

- `-o json`

## JSON-Path Output

`-o jsonpath` activates a jsonpath output. With `-oJ` you can apply the jsonpath filter which will be applied.
For this [jsonpath-ng](https://pypi.org/project/jsonpath-ng/) is used. There you can find further information about the filter format.

## Template Output

TODO

## Raw Output

TODO

