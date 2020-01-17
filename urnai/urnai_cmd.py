# -*- coding: utf-8 -*-
from utils import error.*
from runner.runnerbuilder import RunnerBuilder
from runner.parserbuilder import ParserBuilder

def main():
    parser = ParserBuilder.DefaultParser()
    runner = RunnerBuilder.build(parser)

    runner.run()