# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from sys import (exit)
from .macros import macros, pre_class  # noqa: F401
from .gs import (GS)
from .optionable import Optionable
from .kiplot import check_eeschema_do, exec_with_retry, load_sch
from .error import (KiPlotConfigurationError)
from .misc import (CMD_EESCHEMA_DO, ERC_ERROR)
from .log import (get_logger)

logger = get_logger(__name__)


@pre_class
class Run_ERC(BasePreFlight):  # noqa: F821
    """ [boolean=false] Runs the ERC (Electrical Rules Check). To ensure the schematic is electrically correct.
        The report file name is controlled by the global output pattern (%i=erc %x=txt) """
    def __init__(self, name, value):
        super().__init__(name, value)
        if not isinstance(value, bool):
            raise KiPlotConfigurationError('must be boolean')
        self._enabled = value
        self._sch_related = True

    def get_targets(self):
        """ Returns a list of targets generated by this preflight """
        load_sch()
        return [Optionable.expand_filename_sch(None, GS.out_dir, GS.def_global_output, 'erc', 'txt')]

    def run(self):
        check_eeschema_do()
        # The schematic is loaded only before executing an output related to it.
        # But here we need data from it.
        output = self.get_targets()[0]
        logger.debug('ERC report: '+output)
        cmd = [CMD_EESCHEMA_DO, 'run_erc', '-o', output]
        if GS.filter_file:
            cmd.extend(['-f', GS.filter_file])
        cmd.extend([GS.sch_file, GS.out_dir])
        # If we are in verbose mode enable debug in the child
        if GS.debug_enabled:
            cmd.insert(1, '-vv')
            cmd.insert(1, '-r')
        logger.info('- Running the ERC')
        ret = exec_with_retry(cmd)
        if ret:
            if ret > 127:
                ret = -(256-ret)
            if ret < 0:
                logger.error('ERC errors: %d', -ret)
            else:
                logger.error('ERC returned %d', ret)
            exit(ERC_ERROR)
