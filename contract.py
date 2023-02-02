#!/usr/bin/env python3
from pyteal import *
from beaker import *
import os
import json
from typing import Final


class DAO(Application):
    Creator: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.bytes, default=Global.creator_address()
    )

    RegBegin: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.uint64, default=Int(0)
    )

    RegEnd: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.uint64, default=Int(0)
    )

    VoteBegin: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.uint64, default=Int(0)
    )

    VoteEnd: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.uint64, default=Int(0)
    )

    voter_token: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.uint64, default=Int(0)
    )

    yes: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.uint64, default=Int(0)
    )

    no: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.uint64, default=Int(0)
    )

    vote: Final[AccountStateValue] = AccountStateValue(
        stack_type=TealType.bytes, default=Bytes("")
    )

    @create
    def create(self, voter_token: abi.Asset):
        return Seq(
            Assert(Txn.application_args.length() == Int(4)),
            self.initialize_application_state(),
            self.RegBegin.set(Txn.application_args[0]),
            self.RegEnd.set(Txn.application_args[1]),
            self.VoteBegin.set(Txn.application_args[2]),
            self.VoteEnd.set(Txn.application_args[3]),
            self.voter_token.set(voter_token.asset_id()),
        )

    @opt_in
    def opt_in(self):
        return Seq(
            And(
                Global.round() >= App.globalGet(Bytes("RegBegin")),
                Global.round() <= App.globalGet(Bytes("RegEnd")),
            )
        )

    @external
    def vote(self, voter_token: abi.Asset, vote: abi.String):
        get_voter_holding = (AssetHolding.balance(Int(0), Txn.assets[0]),)
        return Seq(
            # assert that the asset in the foreignAssets array is the voter token
            Assert(voter_token.asset_id() == self.voter_token_id.get()),
            # assert that voter token is held by sender
            voter_token.holding(Txn.sender())
            .balance()
            .outputReducer(
                lambda value, has_value: Assert(And(has_value, value > Int(0)))
            ),
            # assert that voting period is active
            Assert(Global.latest_timestamp() >= self.vote_begin.get()),
            Assert(Global.latest_timestamp() < self.vote_end.get()),
            # increment yes or no based on vote
            If(vote.get() == Bytes("yes"))
            .Then(self.yes.set(self.yes.get() + Int(1)))
            .ElseIf(vote.get() == Bytes("no"))
            .Then(self.no.set(self.no.get() + Int(1)))
            .Else(Approve()),
        )

if __name__ == "__main__":
    DAO().dump("artifacts")
