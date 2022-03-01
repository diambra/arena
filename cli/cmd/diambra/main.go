package main

import (
	"os"

	"github.com/diambra/diambraArena/cli/commands"

	"github.com/urfave/cli/v2"
)

func main() {
	app := &cli.App{
		Name: "diambra",
		Commands: []*cli.Command{
			{
				Name:   "run",
				Action: commands.Run,
			},
		},
	}
	app.Run(os.Args)
}
