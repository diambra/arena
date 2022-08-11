# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import diambra.arena.engine.interface_pb2 as interface__pb2


class EnvServerStub(object):
    """The DIAMBRA service definition.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetError = channel.unary_unary(
                '/interface.EnvServer/GetError',
                request_serializer=interface__pb2.Empty.SerializeToString,
                response_deserializer=interface__pb2.ErrorMessage.FromString,
                )
        self.EnvInit = channel.unary_unary(
                '/interface.EnvServer/EnvInit',
                request_serializer=interface__pb2.EnvSettings.SerializeToString,
                response_deserializer=interface__pb2.EnvInfoAndIntData.FromString,
                )
        self.Reset = channel.unary_unary(
                '/interface.EnvServer/Reset',
                request_serializer=interface__pb2.Empty.SerializeToString,
                response_deserializer=interface__pb2.Obs.FromString,
                )
        self.Step1P = channel.unary_unary(
                '/interface.EnvServer/Step1P',
                request_serializer=interface__pb2.Command.SerializeToString,
                response_deserializer=interface__pb2.Obs.FromString,
                )
        self.Step2P = channel.unary_unary(
                '/interface.EnvServer/Step2P',
                request_serializer=interface__pb2.Command.SerializeToString,
                response_deserializer=interface__pb2.Obs.FromString,
                )
        self.Close = channel.unary_unary(
                '/interface.EnvServer/Close',
                request_serializer=interface__pb2.Empty.SerializeToString,
                response_deserializer=interface__pb2.Empty.FromString,
                )


class EnvServerServicer(object):
    """The DIAMBRA service definition.
    """

    def GetError(self, request, context):
        """Receives back environment error message
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def EnvInit(self, request, context):
        """Sends environment settings, receives back environment info and int data vars
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Reset(self, request, context):
        """Call reset method, receives observation (containing also player ID in this case)
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Step1P(self, request, context):
        """Call step method (1P), receives observation
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Step2P(self, request, context):
        """Call step method (2P), receives observation
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Close(self, request, context):
        """Call close method, receives observation placeholder
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_EnvServerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetError': grpc.unary_unary_rpc_method_handler(
                    servicer.GetError,
                    request_deserializer=interface__pb2.Empty.FromString,
                    response_serializer=interface__pb2.ErrorMessage.SerializeToString,
            ),
            'EnvInit': grpc.unary_unary_rpc_method_handler(
                    servicer.EnvInit,
                    request_deserializer=interface__pb2.EnvSettings.FromString,
                    response_serializer=interface__pb2.EnvInfoAndIntData.SerializeToString,
            ),
            'Reset': grpc.unary_unary_rpc_method_handler(
                    servicer.Reset,
                    request_deserializer=interface__pb2.Empty.FromString,
                    response_serializer=interface__pb2.Obs.SerializeToString,
            ),
            'Step1P': grpc.unary_unary_rpc_method_handler(
                    servicer.Step1P,
                    request_deserializer=interface__pb2.Command.FromString,
                    response_serializer=interface__pb2.Obs.SerializeToString,
            ),
            'Step2P': grpc.unary_unary_rpc_method_handler(
                    servicer.Step2P,
                    request_deserializer=interface__pb2.Command.FromString,
                    response_serializer=interface__pb2.Obs.SerializeToString,
            ),
            'Close': grpc.unary_unary_rpc_method_handler(
                    servicer.Close,
                    request_deserializer=interface__pb2.Empty.FromString,
                    response_serializer=interface__pb2.Empty.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'interface.EnvServer', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class EnvServer(object):
    """The DIAMBRA service definition.
    """

    @staticmethod
    def GetError(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/interface.EnvServer/GetError',
            interface__pb2.Empty.SerializeToString,
            interface__pb2.ErrorMessage.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def EnvInit(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/interface.EnvServer/EnvInit',
            interface__pb2.EnvSettings.SerializeToString,
            interface__pb2.EnvInfoAndIntData.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Reset(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/interface.EnvServer/Reset',
            interface__pb2.Empty.SerializeToString,
            interface__pb2.Obs.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Step1P(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/interface.EnvServer/Step1P',
            interface__pb2.Command.SerializeToString,
            interface__pb2.Obs.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Step2P(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/interface.EnvServer/Step2P',
            interface__pb2.Command.SerializeToString,
            interface__pb2.Obs.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Close(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/interface.EnvServer/Close',
            interface__pb2.Empty.SerializeToString,
            interface__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
