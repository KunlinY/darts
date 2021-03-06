""" Config class for search/augment """
import argparse
import os
import genotypes as gt
from functools import partial
import torch


def get_parser(name):
    """ make default formatted parser """
    parser = argparse.ArgumentParser(name, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # print default value always
    parser.add_argument = partial(parser.add_argument, help=' ')
    return parser


def parse_gpus(gpus):
    if gpus == 'all':
        return list(range(torch.cuda.device_count()))
    else:
        return [int(s) for s in gpus.split(',')]


class BaseConfig(argparse.Namespace):
    def print_params(self, prtf=print):
        prtf("")
        prtf("Parameters:")
        for attr, value in sorted(vars(self).items()):
            prtf("{}={}".format(attr.upper(), value))
        prtf("")

    def as_markdown(self):
        """ Return configs as markdown format """
        text = "|name|value|  \n|-|-|  \n"
        for attr, value in sorted(vars(self).items()):
            text += "|{}|{}|  \n".format(attr, value)

        return text


class SearchConfig(BaseConfig):
    def build_parser(self):
        parser = get_parser("Search config")
        parser.add_argument('--name', required=True)
        parser.add_argument('--dataset', required=True, help='CIFAR10 / MNIST / FashionMNIST')
        parser.add_argument('--batch_size', type=int, default=64, help='batch size')
        parser.add_argument('--w_lr', type=float, default=0.025, help='lr for weights')
        parser.add_argument('--w_lr_min', type=float, default=0.001, help='minimum lr for weights')
        parser.add_argument('--w_momentum', type=float, default=0.9, help='momentum for weights')
        parser.add_argument('--w_weight_decay', type=float, default=3e-4,
                            help='weight decay for weights')
        parser.add_argument('--w_grad_clip', type=float, default=5.,
                            help='gradient clipping for weights')
        parser.add_argument('--print_freq', type=int, default=50, help='print frequency')
        parser.add_argument('--gpus', default='0', help='gpu device ids separated by comma. '
                            '`all` indicates use all gpus.')
        parser.add_argument('--epochs', type=int, default=50, help='# of training epochs')
        parser.add_argument('--init_channels', type=int, default=16)
        parser.add_argument('--layers', type=int, default=8, help='# of layers')
        parser.add_argument('--seed', type=int, default=2, help='random seed')
        parser.add_argument('--workers', type=int, default=4, help='# of workers')
        parser.add_argument('--alpha_lr', type=float, default=3e-4, help='lr for alpha')
        parser.add_argument('--alpha_weight_decay', type=float, default=1e-3,
                            help='weight decay for alpha')
        parser.add_argument('--noise', type=bool, default=False, help='add noise or not')
        parser.add_argument(
            "--world_size",
            type=int,
            default=4,
            help="""Total number of participating processes. Should be the sum of
                master node and all training nodes.""")
        parser.add_argument(
            "--rank",
            type=int,
            default=None,
            help="Global rank of this process. Pass in 0 for master.")
        parser.add_argument(
            "--num_gpus",
            type=int,
            default=0,
            help="""Number of GPUs to use for training, Currently supports between 0
                 and 2 GPUs. Note that this argument will be passed to the parameter servers.""")
        parser.add_argument(
            "--master_addr",
            type=str,
            default="server-kl",
            help="""Address of master, will default to localhost if not provided.
                Master must be able to accept network traffic on the address + port.""")
        parser.add_argument(
            "--master_port",
            type=str,
            default="80",
            help="""Port that master is listening on, will default to 29500 if not
                provided. Master must be able to accept network traffic on the host and port.""")

        return parser

    def __init__(self):
        parser = self.build_parser()
        args = parser.parse_args()
        super().__init__(**vars(args))

        self.gpus = parse_gpus(self.gpus)
        self.batch_size = self.world_size * self.batch_size
        self.w_lr = self.world_size * self.w_lr
        self.w_lr_min = self.world_size * self.w_lr_min
        self.alpha_lr = self.world_size * self.alpha_lr
        # self.workers = len(self.gpus) * self.workers
        self.data_path = './data/'
        self.path = os.path.join('searchs_fl_%d_%d_%s' % (self.world_size, self.rank, self.noise), self.name)
        self.plot_path = os.path.join(self.path, 'plots')


class AugmentConfig(BaseConfig):
    def build_parser(self):
        parser = get_parser("Augment config")
        parser.add_argument('--name', required=True)
        parser.add_argument('--dataset', required=True, help='CIFAR10 / MNIST / FashionMNIST')
        parser.add_argument('--batch_size', type=int, default=96, help='batch size')
        parser.add_argument('--lr', type=float, default=0.025, help='lr for weights')
        parser.add_argument('--momentum', type=float, default=0.9, help='momentum')
        parser.add_argument('--weight_decay', type=float, default=3e-4, help='weight decay')
        parser.add_argument('--grad_clip', type=float, default=5.,
                            help='gradient clipping for weights')
        parser.add_argument('--print_freq', type=int, default=200, help='print frequency')
        parser.add_argument('--gpus', default='0', help='gpu device ids separated by comma. '
                            '`all` indicates use all gpus.')
        parser.add_argument('--epochs', type=int, default=600, help='# of training epochs')
        parser.add_argument('--init_channels', type=int, default=36)
        parser.add_argument('--layers', type=int, default=20, help='# of layers')
        parser.add_argument('--seed', type=int, default=2, help='random seed')
        parser.add_argument('--workers', type=int, default=4, help='# of workers')
        parser.add_argument('--aux_weight', type=float, default=0.4, help='auxiliary loss weight')
        parser.add_argument('--cutout_length', type=int, default=16, help='cutout length')
        parser.add_argument('--drop_path_prob', type=float, default=0.2, help='drop path prob')

        parser.add_argument('--genotype', required=True, help='Cell genotype')
        parser.add_argument('--noise', type=bool, default=False, help='add noise or not')

        return parser

    def __init__(self):
        parser = self.build_parser()
        args = parser.parse_args()
        super().__init__(**vars(args))

        self.gpus = parse_gpus(self.gpus)
        self.data_path = './data/'
        self.path = os.path.join('searchs_%d_%s' % (len(self.gpus), self.noise), self.name)
        self.genotype = gt.from_str(self.genotype)
